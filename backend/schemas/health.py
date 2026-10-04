from typing import Literal

from pydantic import BaseModel

ServiceStatus = Literal["ok", "unavailable"]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    api: Literal["ok"]
    postgres: ServiceStatus
    neo4j: ServiceStatus
    detail: str | None = None
