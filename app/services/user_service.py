from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from tortoise.exceptions import DoesNotExist

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models import User


async def get_user_by_username(username: str) -> Optional[User]:
    try:
        return await User.get(username=username)
    except DoesNotExist:
        return None


async def create_default_admin() -> User:
    user = await get_user_by_username("admin")
    if user:
        return user
    password_hash = hash_password(settings.admin_initial_password)
    user = await User.create(
        username="admin",
        password_hash=password_hash,
        is_admin=True,
        is_active=True,
    )
    return user


async def authenticate_user(username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(username)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def update_password(user: User, new_password: str) -> User:
    user.password_hash = hash_password(new_password)
    await user.save(update_fields=["password_hash", "updated_at"])
    return user


async def mark_user_login(user: User) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    await user.save(update_fields=["last_login_at", "updated_at"])

