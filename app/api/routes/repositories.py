from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.dependencies.auth import (
    get_current_active_user,
    get_current_admin_user,
    get_optional_user,
)
from app.models import Repository, OperationLog, User, PullPushEvent
from app.schemas import RepositoryRead, RepositoryUpdate
from app.services import get_registry_client, RegistryNotFoundError


router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("/", response_model=list[RepositoryRead], summary="列出仓库")
async def list_repositories(user: User | None = Depends(get_optional_user)) -> list[RepositoryRead]:
    client = get_registry_client()
    repo_names = await client.list_repositories()
    existing = {r.name: r async for r in Repository.all()}

    # 统计每个仓库的标签数
    tags_count_map: dict[str, int] = {}
    for name in repo_names:
        try:
            tags_count_map[name] = len(await client.list_tags(name))
        except RegistryNotFoundError:
            tags_count_map[name] = 0

    result: list[RepositoryRead] = []
    for name in repo_names:
        repo = existing.get(name)
        # 需求：public 下的镜像全部公开
        under_public = name.startswith("public/") or name == "public"
        if repo:
            if under_public and not repo.is_public:
                repo.is_public = True
                await repo.save(update_fields=["is_public", "updated_at"])
            is_public = repo.is_public
        else:
            # 创建缺失记录，默认 public 下为公开
            defaults = {"is_public": True} if under_public else {"is_public": False}
            repo, _ = await Repository.get_or_create(name=name, defaults=defaults)
            is_public = repo.is_public
        if user is None and not is_public:
            continue
        result.append(RepositoryRead(name=name, is_public=is_public, tags_count=tags_count_map.get(name, 0)))
    return sorted(result, key=lambda r: r.name)


@router.get("/{name:path}/tags", summary="仓库标签列表")
async def list_tags(name: str, user: User | None = Depends(get_optional_user)) -> dict:
    client = get_registry_client()
    repo = await Repository.get_or_create(name=name)
    repo_obj = repo[0]
    if name.startswith("public/") or name == "public":
        if not repo_obj.is_public:
            repo_obj.is_public = True
            await repo_obj.save(update_fields=["is_public", "updated_at"])
    if user is None and not repo_obj.is_public:
        raise HTTPException(status_code=403, detail="该仓库为私有，需登录访问")
    try:
        tags = await client.list_tags(name)
    except RegistryNotFoundError:
        raise HTTPException(status_code=404, detail="仓库不存在")
    return {"repository": name, "tags": tags}


@router.get("/{name:path}/manifests/{reference}", summary="获取 manifest 元数据")
async def get_manifest(name: str, reference: str, user: User | None = Depends(get_optional_user)) -> dict:
    client = get_registry_client()
    repo = await Repository.get_or_create(name=name)
    repo_obj = repo[0]
    if user is None and not repo_obj.is_public:
        raise HTTPException(status_code=403, detail="该仓库为私有，需登录访问")
    try:
        meta = await client.get_manifest(name, reference)
    except RegistryNotFoundError:
        raise HTTPException(status_code=404, detail="镜像或标签不存在")
    # stats
    push_event = await PullPushEvent.filter(repository=name, tag=reference, action="push").order_by("-created_at").first()
    last_pull_event = await PullPushEvent.filter(repository=name, tag=reference, action="pull").order_by("-created_at").first()
    pull_count = await PullPushEvent.filter(repository=name, tag=reference, action="pull").count()
    return {
        "repository": name,
        "reference": reference,
        "digest": meta.digest,
        "media_type": meta.media_type,
        "size_bytes": meta.size_bytes,
        "architecture": meta.architecture,
        "os": meta.os,
        "created_at": meta.created_at,
        "push_time": push_event.created_at if push_event else None,
        "last_pull_time": last_pull_event.created_at if last_pull_event else None,
        "pull_count": pull_count,
        "pull_command": f"docker pull {settings.registry_url.rstrip('/')}/{name}:{reference}",
    }


@router.put("/{name:path}", response_model=RepositoryRead, summary="更新仓库可见性")
async def update_repository_visibility(
    name: str,
    payload: RepositoryUpdate,
    admin: User = Depends(get_current_admin_user),
) -> RepositoryRead:
    repo, _created = await Repository.get_or_create(name=name)
    repo.is_public = payload.is_public
    await repo.save(update_fields=["is_public", "updated_at"])
    await OperationLog.create(
        actor=admin.username,
        action="repo.update_visibility",
        target=name,
        detail=f"is_public={payload.is_public}",
    )
    return RepositoryRead(name=repo.name, is_public=repo.is_public)


@router.get("/{name:path}/stats", summary="仓库统计")
async def repository_stats(name: str, user: User | None = Depends(get_optional_user)) -> dict:
    client = get_registry_client()
    repo = await Repository.get_or_create(name=name)
    repo_obj = repo[0]
    if user is None and not repo_obj.is_public:
        raise HTTPException(status_code=403, detail="该仓库为私有，需登录访问")
    try:
        tags = await client.list_tags(name)
    except RegistryNotFoundError:
        raise HTTPException(status_code=404, detail="仓库不存在")
    total_size = 0
    for tag in tags:
        try:
            meta = await client.get_manifest(name, tag)
            total_size += meta.size_bytes
        except RegistryNotFoundError:
            # skip missing
            continue
    return {
        "repository": name,
        "tag_count": len(tags),
        "size_bytes": total_size,
        "is_public": repo_obj.is_public,
    }