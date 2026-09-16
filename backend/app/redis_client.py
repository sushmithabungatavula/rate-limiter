import redis.asyncio as redis

from .config import REDIS_HOST, REDIS_PORT, REDIS_URL

if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
else:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
