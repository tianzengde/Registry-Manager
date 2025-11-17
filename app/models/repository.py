from __future__ import annotations

from tortoise import fields, models


class Repository(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=256, unique=True)
    is_public = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "repositories"

    def __str__(self) -> str:
        return self.name