import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.redis_client import redis_client


@pytest_asyncio.fixture(autouse=True)
async def flush_redis():
    await redis_client.flushdb()
    yield
    await redis_client.flushdb()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
