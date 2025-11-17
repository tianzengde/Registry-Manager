from __future__ import annotations

from tortoise import fields, models


class OperationLog(models.Model):
    id = fields.IntField(pk=True)
    actor = fields.CharField(max_length=64)
    action = fields.CharField(max_length=64)
    target = fields.CharField(max_length=256)
    detail = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "operation_logs"