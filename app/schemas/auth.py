from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")


class TokenPayload(BaseModel):
    sub: str
    exp: int


class LoginRequest(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    username: str
    is_admin: bool
    last_login_at: Optional[datetime]
    created_at: datetime


class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str

