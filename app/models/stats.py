from __future__ import annotations

from datetime import date

from tortoise import fields, models


class PullPushEvent(models.Model):
    id = fields.IntField(pk=True)
    repository = fields.CharField(max_length=256)
    tag = fields.CharField(max_length=128, null=True)
    action = fields.CharField(max_length=16)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "pull_push_events"


class RepoDailyStats(models.Model):
    id = fields.IntField(pk=True)
    repository = fields.CharField(max_length=256)
    day = fields.DateField()
    pulls = fields.IntField(default=0)
    pushes = fields.IntField(default=0)
    last_activity_at = fields.DatetimeField(null=True)

    class Meta:
        table = "repo_daily_stats"
        unique_together = ("repository", "day")