from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.models import User
from app.services import authenticate_user, get_user_by_username


# auto_error=False 由我们手动控制 401 响应，不返回 WWW-Authenticate 头
basic_security = HTTPBasic(auto_error=False)


async def _get_user_from_credentials(
    credentials: HTTPBasicCredentials,
) -> User:
    """Authenticate user from Basic Auth credentials and return User."""
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已被禁用")
    return user


async def get_current_active_user(
    credentials: Optional[HTTPBasicCredentials] = Depends(basic_security),
) -> User:
    """
    获取当前已认证的用户。
    所有需要认证的 API 端点使用此依赖。
    手动验证 Basic Auth 凭证，避免浏览器弹出原生登录框。
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请提供认证信息",
        )
    return await _get_user_from_credentials(credentials)


async def get_current_admin_user(
    credentials: Optional[HTTPBasicCredentials] = Depends(basic_security),
) -> User:
    """
    获取当前管理员用户。
    仅管理员可访问的端点使用此依赖。
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请提供认证信息",
        )
    user = await _get_user_from_credentials(credentials)
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user


async def get_optional_user(
    request: Request,
) -> Optional[User]:
    """
    获取当前用户（可选），未提供凭证则返回 None。
    用于公开端点但需要识别已登录用户的场景。
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        return None
    try:
        import base64
        encoded = auth_header[6:]
        decoded = base64.b64decode(encoded.encode()).decode("utf-8")
        if ":" not in decoded:
            return None
        username, password = decoded.split(":", 1)
        user = await authenticate_user(username, password)
        return user
    except Exception:
        return None


def credentials_from_request(request: Request) -> Optional[HTTPBasicCredentials]:
    """Extract Basic Auth credentials from request headers."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        return None
    try:
        import base64
        encoded = auth_header[6:]
        decoded = base64.b64decode(encoded.encode()).decode("utf-8")
        if ":" not in decoded:
            return None
        username, password = decoded.split(":", 1)
        return HTTPBasicCredentials(username=username, password=password)
    except Exception:
        return None