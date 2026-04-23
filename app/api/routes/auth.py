from __future__ import annotations

from base64 import b64decode
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.dependencies.auth import get_current_active_user, get_current_admin_user
from app.models import User
from app.schemas import UserRead
from app.models import OperationLog
from app.services import authenticate_user, mark_user_login, update_password
from app.schemas.auth import PasswordUpdateRequest


basic_security = HTTPBasic()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserRead, summary="获取当前用户信息（统一认证入口）")
async def get_current_user_info(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
) -> UserRead:
    """
    统一 Basic Auth 认证入口。
    Web 前端和 Docker Client 共用同一套凭证。
    验证通过后返回用户信息，前端存储 { username, password } 于 localStorage。
    """
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已被禁用")
    await mark_user_login(user)
    await OperationLog.create(
        actor=user.username,
        action="login",
        target="auth",
        detail="Web 登录",
    )
    return UserRead(
        username=user.username,
        is_admin=user.is_admin,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.post("/password", summary="修改密码")
async def change_password(
    payload: PasswordUpdateRequest,
    user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """
    已登录用户修改自身密码。
    必须验证当前密码，新密码至少 6 字符，修改后即时生效。
    """
    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少为 6 个字符",
        )
    # Verify current password using Basic Auth credentials already checked by dependency
    # The user object from get_current_active_user is already authenticated
    current_ok = await authenticate_user(user.username, payload.current_password)
    if not current_ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码不正确",
        )
    await update_password(user, payload.new_password)
    await OperationLog.create(
        actor=user.username,
        action="password",
        target="auth",
        detail="修改密码",
    )
    return {"detail": "密码已更新"}


@router.get("/check", summary="轻量级认证检查")
async def check_auth(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
) -> dict:
    """
    轻量级认证检查端点，用于 Docker login 场景。
    验证成功返回 200，失败返回 401。
    """
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"username": user.username, "is_admin": user.is_admin}