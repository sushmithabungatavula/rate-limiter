from typing import Optional

from pydantic import BaseModel


class CheckRequest(BaseModel):
    client_id: str
    algorithm: str
    limit: int
    window_seconds: int


class CheckResponse(BaseModel):
    allowed: bool
    remaining: int
    reset_in_seconds: int
    requests_in_window: int
    is_throttled: bool


class ResetRequest(BaseModel):
    client_id: str
    algorithm: Optional[str] = None


class ResetResponse(BaseModel):
    status: str
    client_id: str


class HealthResponse(BaseModel):
    status: str
    redis: str


class ClientInfo(BaseModel):
    client_id: str
    algorithm: str
    requests_in_window: int
    remaining: int
    is_throttled: bool


class ClientsResponse(BaseModel):
    clients: list[ClientInfo]


class StatsResponse(BaseModel):
    total_active_clients: int
    requests_last_60s: int
    throttled_last_60s: int
    redis_status: str
