# Distributed Rate Limiter

A rate-limiting service that gates requests per client using either a token
bucket or a sliding window algorithm, backed by Redis for shared, atomic
state. It ships with a FastAPI backend, a live React dashboard for watching
and generating traffic, and a full test suite.

## Architecture

```
Client -> POST /check -> FastAPI -> Lua Script -> Redis   (token bucket)
Client -> POST /check -> FastAPI -> Pipeline+WATCH -> Redis (sliding window)
                              |
                              v
                     SSE /stream (1s tick) -> React Dashboard
```

## How to run

```bash
docker compose up --build
```

This starts three services:

| Service  | URL                     |
|----------|-------------------------|
| frontend | http://localhost:3000   |
| backend  | http://localhost:8000   |
| redis    | localhost:6379          |

## API reference

### `POST /check`

Request:

```json
{
  "client_id": "user_123",
  "algorithm": "token_bucket",
  "limit": 10,
  "window_seconds": 60
}
```

`algorithm` is `token_bucket` or `sliding_window`.

Response `200`:

```json
{
  "allowed": true,
  "remaining": 9,
  "reset_in_seconds": 0,
  "requests_in_window": 1,
  "is_throttled": false
}
```

`400` if `algorithm` is not one of the two supported values. `422` if a
required field is missing or the wrong type.

```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"client_id":"user_123","algorithm":"token_bucket","limit":10,"window_seconds":60}'
```

### `DELETE /reset`

Clears a client's state so its next request starts fresh.

```json
{ "client_id": "user_123", "algorithm": "token_bucket" }
```

Omit `algorithm` to reset both algorithms' state for that client.

```bash
curl -X DELETE http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"client_id":"user_123","algorithm":"token_bucket"}'
```

### `GET /health`

```bash
curl http://localhost:8000/health
# {"status":"ok","redis":"connected"}
```

### `GET /clients`

Read-only snapshot of every client seen in the last 5 minutes, used by the
dashboard's live table.

```bash
curl http://localhost:8000/clients
```

### `GET /stats`

Aggregate counters for the dashboard's header cards.

```bash
curl http://localhost:8000/stats
# {"total_active_clients":2,"requests_last_60s":21,"throttled_last_60s":15,"redis_status":"connected"}
```

### `GET /stream`

Server-Sent Events stream combining `/stats` and `/clients`, pushed once per
second, for the dashboard to render live without polling.

```bash
curl -N http://localhost:8000/stream
```

## Algorithms

### Token bucket

```
[Limit: 10 tokens]
|████████░░| 8/10
Each request consumes 1 token.
Tokens refill over time.
Allows short bursts up to limit.
```

Good for APIs where occasional bursts are acceptable. Tokens accumulate when
traffic is low and get spent during spikes. Capacity is `limit` tokens,
refilling continuously at `limit / window_seconds` tokens per second.

### Sliding window

```
60 second window
|--[req][req][req][req]--|
     oldest            now
Evicts requests older than window.
Strict limit at all times.
```

Strict and fair. No bursts allowed beyond the limit. Every request is
counted within a rolling time window; requests older than `window_seconds`
are evicted before each check.

## How race conditions are handled

**Token bucket** runs entirely inside a single Lua script executed with
`EVAL`. Redis executes Lua scripts atomically, so the read-refill-consume-
write sequence for a given client can never be interleaved with another
request for that same client, even under concurrent load.

**Sliding window** uses a Redis sorted set (`ZSET`) per client, scored by
request timestamp, combined with optimistic locking: the client key is
`WATCH`ed, the count of requests in the current window is read, and only if
that count is under the limit is the new request added inside a `MULTI`/
`EXEC` pipeline. If another request slipped in and modified the key between
the `WATCH` and the `EXEC`, Redis aborts the transaction and the check is
retried from scratch. This is what `test_concurrent_requests_respect_limit`
verifies: firing 20 concurrent requests against a limit of 5 allows exactly
5 and denies exactly 15.

## How to run tests

```bash
docker exec backend pytest
```

## Potential improvements

- Per-route rate limits
- Admin UI to configure limits without restart
- Distributed tracing with OpenTelemetry
- Prometheus metrics endpoint
- Rate limit tiers per user plan
