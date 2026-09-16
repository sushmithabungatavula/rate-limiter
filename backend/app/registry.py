import json
import time
import uuid

from .algorithms.token_bucket import peek_token_bucket
from .algorithms.sliding_window import peek_sliding_window
from .config import STALE_CLIENT_SECONDS
from .redis_client import redis_client

REGISTRY_KEY = "registry:clients"
GLOBAL_REQUESTS_KEY = "global:requests"
GLOBAL_THROTTLED_KEY = "global:throttled"
STATS_WINDOW_SECONDS = 60

PEEK_FNS = {
    "token_bucket": peek_token_bucket,
    "sliding_window": peek_sliding_window,
}


async def record_request(client_id: str, algorithm: str, limit: int, window_seconds: int, allowed: bool) -> None:
    now = time.time()
    entry = json.dumps(
        {
            "algorithm": algorithm,
            "limit": limit,
            "window_seconds": window_seconds,
            "last_seen": now,
        }
    )
    pipe = redis_client.pipeline(transaction=False)
    pipe.hset(REGISTRY_KEY, client_id, entry)
    pipe.zadd(GLOBAL_REQUESTS_KEY, {f"{now}:{uuid.uuid4().hex}": now})
    if not allowed:
        pipe.zadd(GLOBAL_THROTTLED_KEY, {f"{now}:{uuid.uuid4().hex}": now})
    await pipe.execute()


async def reset_client(client_id: str, algorithm: str | None = None) -> None:
    keys = []
    if algorithm in (None, "token_bucket"):
        keys.append(f"tb:{client_id}")
    if algorithm in (None, "sliding_window"):
        keys.append(f"sw:{client_id}")
    if keys:
        await redis_client.delete(*keys)
    if algorithm is None:
        await redis_client.hdel(REGISTRY_KEY, client_id)


async def get_active_clients() -> list[dict]:
    raw = await redis_client.hgetall(REGISTRY_KEY)
    now = time.time()
    clients = []
    stale_ids = []

    for client_id, raw_entry in raw.items():
        entry = json.loads(raw_entry)
        if now - entry["last_seen"] > STALE_CLIENT_SECONDS:
            stale_ids.append(client_id)
            continue

        peek_fn = PEEK_FNS[entry["algorithm"]]
        state = await peek_fn(client_id, entry["limit"], entry["window_seconds"])
        clients.append(
            {
                "client_id": client_id,
                "algorithm": entry["algorithm"],
                **state,
            }
        )

    if stale_ids:
        await redis_client.hdel(REGISTRY_KEY, *stale_ids)

    return clients


async def get_stats() -> dict:
    now = time.time()
    window_start = now - STATS_WINDOW_SECONDS

    await redis_client.zremrangebyscore(GLOBAL_REQUESTS_KEY, 0, window_start)
    await redis_client.zremrangebyscore(GLOBAL_THROTTLED_KEY, 0, window_start)

    requests_last_60s = await redis_client.zcard(GLOBAL_REQUESTS_KEY)
    throttled_last_60s = await redis_client.zcard(GLOBAL_THROTTLED_KEY)

    raw = await redis_client.hgetall(REGISTRY_KEY)
    total_active_clients = sum(
        1 for entry in raw.values() if now - json.loads(entry)["last_seen"] <= STALE_CLIENT_SECONDS
    )

    try:
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"

    return {
        "total_active_clients": total_active_clients,
        "requests_last_60s": requests_last_60s,
        "throttled_last_60s": throttled_last_60s,
        "redis_status": redis_status,
    }
