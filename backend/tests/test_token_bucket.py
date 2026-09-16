import asyncio

import pytest

from app.algorithms.token_bucket import check_token_bucket

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_first_request_allowed():
    result = await check_token_bucket("client_tb_1", limit=5, window_seconds=60)
    assert result["allowed"] is True


async def test_requests_within_limit_allowed():
    client_id = "client_tb_2"
    for _ in range(5):
        result = await check_token_bucket(client_id, limit=5, window_seconds=60)
        assert result["allowed"] is True


async def test_request_over_limit_denied():
    client_id = "client_tb_3"
    for _ in range(5):
        await check_token_bucket(client_id, limit=5, window_seconds=60)
    result = await check_token_bucket(client_id, limit=5, window_seconds=60)
    assert result["allowed"] is False


async def test_bucket_refills_after_window():
    client_id = "client_tb_4"
    limit = 2
    window_seconds = 1

    for _ in range(limit):
        await check_token_bucket(client_id, limit=limit, window_seconds=window_seconds)
    denied = await check_token_bucket(client_id, limit=limit, window_seconds=window_seconds)
    assert denied["allowed"] is False

    await asyncio.sleep(1.1)

    allowed = await check_token_bucket(client_id, limit=limit, window_seconds=window_seconds)
    assert allowed["allowed"] is True


async def test_remaining_count_decrements_correctly():
    client_id = "client_tb_5"
    limit = 5
    first = await check_token_bucket(client_id, limit=limit, window_seconds=60)
    second = await check_token_bucket(client_id, limit=limit, window_seconds=60)
    assert second["remaining"] == first["remaining"] - 1
