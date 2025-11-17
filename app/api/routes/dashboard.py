from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_admin_user
from app.models import Repository, RepoDailyStats, PullPushEvent, User


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", summary="全局概览")
async def overview(admin: User = Depends(get_current_admin_user)) -> dict:
    # 实际仓库数量以 Registry 返回的真实列表为准
    try:
        from app.services import get_registry_client
        client = get_registry_client()
        repos = await client.list_repositories()
        repo_count = len(repos)
    except Exception:
        repo_count = await Repository.all().count()
    # storage occupancy: best-effort sum via stats (approximate)
    # tag count: approximate by counting events last 30 days unique tags
    last30 = date.today() - timedelta(days=30)
    try:
        pulls_30 = await RepoDailyStats.filter(day__gte=last30).sum("pulls") or 0
    except Exception:
        pulls_30 = 0
    try:
        pushes_30 = await RepoDailyStats.filter(day__gte=last30).sum("pushes") or 0
    except Exception:
        pushes_30 = 0
    latest_events = []
    try:
        latest_events = [
            {
                "repository": e.repository,
                "action": e.action,
                "tag": e.tag,
                "at": e.created_at,
            }
            async for e in PullPushEvent.all().order_by("-created_at").limit(10)
        ]
    except Exception:
        latest_events = []
    return {
        "repository_count": repo_count,
        "pulls_30d": pulls_30,
        "pushes_30d": pushes_30,
        "recent_events": latest_events,
    }


@router.get("/trends/{name}", summary="仓库近 7/30 天趋势")
async def trends(name: str, admin: User = Depends(get_current_admin_user)) -> dict:
    def range_days(days: int):
        start = date.today() - timedelta(days=days - 1)
        return [start + timedelta(days=i) for i in range(days)]

    def collect(days: int):
        day_list = range_days(days)
        result = []
        for d in day_list:
            result.append({
                "day": d.isoformat(),
                "pulls": 0,
                "pushes": 0,
            })
        return {d["day"]: d for d in result}

    stats = await RepoDailyStats.filter(repository=name)
    by_day = {s.day.isoformat(): s for s in stats}

    trend7 = collect(7)
    trend30 = collect(30)
    for key, s in by_day.items():
        if key in trend7:
            trend7[key]["pulls"] = s.pulls
            trend7[key]["pushes"] = s.pushes
        if key in trend30:
            trend30[key]["pulls"] = s.pulls
            trend30[key]["pushes"] = s.pushes

    return {
        "name": name,
        "last7": list(trend7.values()),
        "last30": list(trend30.values()),
    }


@router.get("/top", summary="拉取次数 Top N")
async def top(n: int = 10, admin: User = Depends(get_current_admin_user)) -> dict:
    # Aggregate by repository from all days
    rows = [
        {
            "repository": s.repository,
            "pulls": s.pulls,
        }
        async for s in RepoDailyStats.all()
    ]
    agg: dict[str, int] = {}
    for r in rows:
        agg[r["repository"]] = agg.get(r["repository"], 0) + r["pulls"]
    items = sorted(({"repository": k, "pulls": v} for k, v in agg.items()), key=lambda x: x["pulls"], reverse=True)[:n]
    return {"items": items}