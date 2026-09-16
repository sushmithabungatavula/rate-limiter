import asyncio
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import registry
from .algorithms.sliding_window import check_sliding_window
from .algorithms.token_bucket import check_token_bucket
from .config import CORS_ORIGINS
from .models import (
    CheckRequest,
    CheckResponse,
    ClientsResponse,
    HealthResponse,
    ResetRequest,
    ResetResponse,
    StatsResponse,
)
from .redis_client import redis_client

app = FastAPI(title="Distributed Rate Limiter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

ALGORITHMS = {"token_bucket", "sliding_window"}
STREAM_INTERVAL_SECONDS = 1


@app.post("/check", response_model=CheckResponse)
async def check(req: CheckRequest):
    if req.algorithm not in ALGORITHMS:
        raise HTTPException(status_code=400, detail=f"invalid algorithm: {req.algorithm}")

    if req.algorithm == "token_bucket":
        result = await check_token_bucket(req.client_id, req.limit, req.window_seconds)
    else:
        result = await check_sliding_window(req.client_id, req.limit, req.window_seconds)

    await registry.record_request(
        req.client_id, req.algorithm, req.limit, req.window_seconds, result["allowed"]
    )
    return result


@app.delete("/reset", response_model=ResetResponse)
async def reset(req: ResetRequest):
    if req.algorithm is not None and req.algorithm not in ALGORITHMS:
        raise HTTPException(status_code=400, detail=f"invalid algorithm: {req.algorithm}")

    await registry.reset_client(req.client_id, req.algorithm)
    return {"status": "reset", "client_id": req.client_id}


@app.get("/health", response_model=HealthResponse)
async def health():
    try:
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    return {"status": "ok", "redis": redis_status}


@app.get("/clients", response_model=ClientsResponse)
async def clients():
    return {"clients": await registry.get_active_clients()}


@app.get("/stats", response_model=StatsResponse)
async def stats():
    return await registry.get_stats()


@app.get("/stream")
async def stream():
    async def event_generator():
        while True:
            payload = {
                "stats": await registry.get_stats(),
                "clients": await registry.get_active_clients(),
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(STREAM_INTERVAL_SECONDS)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
