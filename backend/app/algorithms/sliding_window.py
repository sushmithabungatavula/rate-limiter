import time
import uuid

from redis.exceptions import WatchError

from ..redis_client import redis_client


def _window_key(client_id: str) -> str:
    return f"sw:{client_id}"


async def check_sliding_window(client_id: str, limit: int, window_seconds: int) -> dict:
    """Optimistic-locking check-and-consume on a sorted set.

    WATCH the key so a concurrent writer aborts our transaction if it beats
    us to it; we retry until our read (count) and write (add + expire)
    happen atomically relative to every other caller.
    """
    key = _window_key(client_id)
    now = time.time()
    window_start = now - window_seconds

    async with redis_client.pipeline() as pipe:
        while True:
            try:
                await pipe.watch(key)
                await pipe.zremrangebyscore(key, 0, window_start)
                count = await pipe.zcard(key)

                if count < limit:
                    pipe.multi()
                    member = f"{now}:{uuid.uuid4().hex}"
                    pipe.zadd(key, {member: now})
                    pipe.expire(key, window_seconds)
                    await pipe.execute()
                    allowed = True
                    requests_in_window = count + 1
                else:
                    await pipe.unwatch()
                    allowed = False
                    requests_in_window = count
                break
            except WatchError:
                continue

    remaining = max(0, limit - requests_in_window)
    reset_in_seconds = await _reset_in_seconds(key, window_seconds)

    return {
        "allowed": allowed,
        "remaining": remaining,
        "reset_in_seconds": reset_in_seconds,
        "requests_in_window": requests_in_window,
        "is_throttled": not allowed,
    }


async def peek_sliding_window(client_id: str, limit: int, window_seconds: int) -> dict:
    """Read-only view of current window state, without recording a request."""
    key = _window_key(client_id)
    now = time.time()
    window_start = now - window_seconds
    count = await redis_client.zcount(key, window_start, now)
    remaining = max(0, limit - count)
    return {
        "remaining": remaining,
        "requests_in_window": count,
        "is_throttled": count >= limit,
    }


async def _reset_in_seconds(key: str, window_seconds: int) -> int:
    oldest = await redis_client.zrange(key, 0, 0, withscores=True)
    if not oldest:
        return 0
    _, oldest_ts = oldest[0]
    return max(0, int(window_seconds - (time.time() - oldest_ts)))
