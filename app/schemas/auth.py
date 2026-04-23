from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserRead(BaseModel):
    username: str
    is_admin: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime


class PasswordUpdateRequest(BaseModel):
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, description="新密码（至少6位）")