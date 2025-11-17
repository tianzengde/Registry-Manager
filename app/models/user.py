from __future__ import annotations

from datetime import datetime

from tortoise import fields, models


class User(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=64, unique=True)
    password_hash = fields.CharField(max_length=256)
    is_active = fields.BooleanField(default=True)
    is_admin = fields.BooleanField(default=False)
    last_login_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"<User {self.username}>"

    @property
    def is_authenticated(self) -> bool:
        return self.is_active

