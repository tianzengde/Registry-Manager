from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_admin_user
from app.models import OperationLog, User
from app.schemas import RepositoryRead, RepositoryUpdate


router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/operations", summary="操作日志列表")
async def list_operation_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None, description="按操作类型过滤"),
    actor: Optional[str] = Query(None, description="按操作者过滤"),
    admin: User = Depends(get_current_admin_user),
) -> dict:
    """
    查看操作日志（仅管理员）。
    支持按操作类型和操作者过滤。
    """
    qs = OperationLog.all()
    if action:
        qs = qs.filter(action__icontains=action)
    if actor:
        qs = qs.filter(actor__icontains=actor)

    total = await qs.count()
    logs = [
        {
            "id": log.id,
            "actor": log.actor,
            "action": log.action,
            "target": log.target,
            "detail": log.detail,
            "created_at": log.created_at,
        }
        async for log in qs.order_by("-created_at").offset(skip).limit(limit)
    ]
    return {"total": total, "items": logs}