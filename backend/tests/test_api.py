import asyncio

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_post_check_token_bucket_returns_200(client):
    resp = await client.post(
        "/check",
        json={"client_id": "api_1", "algorithm": "token_bucket", "limit": 10, "window_seconds": 60},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {
        "allowed",
        "remaining",
        "reset_in_seconds",
        "requests_in_window",
        "is_throttled",
    }


async def test_post_check_sliding_window_returns_200(client):
    resp = await client.post(
        "/check",
        json={"client_id": "api_2", "algorithm": "sliding_window", "limit": 10, "window_seconds": 60},
    )
    assert resp.status_code == 200


async def test_invalid_algorithm_returns_400(client):
    resp = await client.post(
        "/check",
        json={"client_id": "api_3", "algorithm": "bogus", "limit": 10, "window_seconds": 60},
    )
    assert resp.status_code == 400


async def test_missing_fields_returns_422(client):
    resp = await client.post("/check", json={"client_id": "api_4"})
    assert resp.status_code == 422


async def test_health_endpoint_returns_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_reset_endpoint_clears_state(client):
    client_id = "api_reset"
    body = {"client_id": client_id, "algorithm": "token_bucket", "limit": 1, "window_seconds": 60}

    await client.post("/check", json=body)
    denied = await client.post("/check", json=body)
    assert denied.json()["allowed"] is False

    reset_resp = await client.request(
        "DELETE", "/reset", json={"client_id": client_id, "algorithm": "token_bucket"}
    )
    assert reset_resp.status_code == 200

    allowed_again = await client.post("/check", json=body)
    assert allowed_again.json()["allowed"] is True


async def test_concurrent_requests_respect_limit(client):
    client_id = "api_concurrent"
    body = {"client_id": client_id, "algorithm": "sliding_window", "limit": 5, "window_seconds": 60}

    tasks = [client.post("/check", json=body) for _ in range(20)]
    responses = await asyncio.gather(*tasks)

    allowed = sum(1 for r in responses if r.json()["allowed"] is True)
    denied = sum(1 for r in responses if r.json()["allowed"] is False)

    assert allowed == 5
    assert denied == 15
