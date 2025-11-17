from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.security import create_access_token
from app.dependencies.auth import get_current_active_user
from app.schemas import (
    LoginRequest,
    PasswordUpdateRequest,
    Token,
    UserRead,
)
from app.services import authenticate_user, mark_user_login, update_password

basic_security = HTTPBasic()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token, summary="用户登录获取 Token")
async def login(data: LoginRequest) -> Token:
    user = await authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    await mark_user_login(user)
    token = create_access_token(subject=user.username)
    return Token(access_token=token)


@router.get("/me", response_model=UserRead, summary="获取当前用户信息")
async def read_profile(user=Depends(get_current_active_user)) -> UserRead:
    return UserRead(
        username=user.username,
        is_admin=user.is_admin,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.post("/password", summary="修改密码")
async def change_password(
    payload: PasswordUpdateRequest,
    user=Depends(get_current_active_user),
) -> dict[str, str]:
    if not await authenticate_user(user.username, payload.current_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码不正确")
    await update_password(user, payload.new_password)
    return {"detail": "密码已更新"}


@router.post("/basic-auth", summary="Registry Basic Auth 验证（预览）")
async def registry_basic_auth(
    credentials: HTTPBasicCredentials = Depends(basic_security),
) -> dict[str, str]:
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Basic"},
        )
    await mark_user_login(user)
    return {"detail": "认证成功", "username": user.username}

