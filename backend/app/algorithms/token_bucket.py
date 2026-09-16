import time

from ..redis_client import redis_client

# Atomic check-and-consume: read the bucket, refill it for elapsed time,
# spend a token if one is available, and persist the new state - all in a
# single Lua execution so concurrent callers can never race on the same key.
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local data = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(data[1])
local last_refill = tonumber(data[2])

if tokens == nil then
    tokens = limit
    last_refill = now
end

local rate = limit / window
local elapsed = now - last_refill
if elapsed > 0 then
    tokens = math.min(limit, tokens + elapsed * rate)
    last_refill = now
end

local allowed = 0
if tokens >= 1 then
    tokens = tokens - 1
    allowed = 1
end

redis.call('HMSET', key, 'tokens', tostring(tokens), 'last_refill', tostring(last_refill))
redis.call('EXPIRE', key, math.ceil(window * 2))

local reset_in_seconds = 0
if tokens < 1 then
    reset_in_seconds = math.ceil((1 - tokens) / rate)
end

return {allowed, tostring(tokens), reset_in_seconds}
"""

_script = None


def _bucket_key(client_id: str) -> str:
    return f"tb:{client_id}"


async def _get_script():
    global _script
    if _script is None:
        _script = redis_client.register_script(TOKEN_BUCKET_LUA)
    return _script


async def check_token_bucket(client_id: str, limit: int, window_seconds: int) -> dict:
    script = await _get_script()
    now = time.time()
    allowed, tokens_raw, reset_in_seconds = await script(
        keys=[_bucket_key(client_id)], args=[limit, window_seconds, now]
    )
    remaining = int(float(tokens_raw))
    return {
        "allowed": bool(int(allowed)),
        "remaining": remaining,
        "reset_in_seconds": int(reset_in_seconds),
        "requests_in_window": limit - remaining,
        "is_throttled": not bool(int(allowed)),
    }


async def peek_token_bucket(client_id: str, limit: int, window_seconds: int) -> dict:
    """Read-only view of current bucket state, without consuming a token."""
    data = await redis_client.hmget(_bucket_key(client_id), "tokens", "last_refill")
    tokens_raw, last_refill_raw = data
    if tokens_raw is None:
        tokens = float(limit)
    else:
        rate = limit / window_seconds
        elapsed = time.time() - float(last_refill_raw)
        tokens = min(float(limit), float(tokens_raw) + elapsed * rate)

    remaining = int(tokens)
    return {
        "remaining": remaining,
        "requests_in_window": limit - remaining,
        "is_throttled": remaining < 1,
    }
