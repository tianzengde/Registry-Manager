from __future__ import annotations

import httpx
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", summary="健康检查")
async def health_check() -> JSONResponse:
    """
    健康检查端点。
    检查应用状态及 Registry 连通性。
    """
    registry_status = "ok"
    registry_detail = ""

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.registry_url.rstrip('/')}/v2/")
            if resp.status_code not in (200, 401):
                registry_status = "error"
                registry_detail = f"Registry returned {resp.status_code}"
    except httpx.RequestError as exc:
        registry_status = "error"
        registry_detail = str(exc)

    is_healthy = registry_status == "ok"
    return JSONResponse(
        status_code=status.HTTP_200_OK if is_healthy else 503,
        content={
            "status": "ok" if is_healthy else "degraded",
            "registry": registry_status,
            "registry_detail": registry_detail,
        },
    )
