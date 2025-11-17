from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.dependencies.auth import get_current_active_user, get_current_admin_user
from app.models import User
from app.services import get_registry_client, RegistryNotFoundError


router = APIRouter(prefix="/images", tags=["images"])


@router.delete("/{name}/manifests/{digest}", summary="删除镜像 manifest（需启用删除）")
async def delete_manifest(name: str, digest: str, admin: User = Depends(get_current_admin_user)) -> dict:
    client = get_registry_client()
    try:
        await client.delete_manifest(name, digest)
    except RegistryNotFoundError:
        raise HTTPException(status_code=404, detail="镜像或仓库不存在")
    return {"detail": "删除已提交", "repository": name, "digest": digest}


@router.delete("/{name}/tags/{tag}", summary="删除镜像标签（需启用删除）")
async def delete_tag(name: str, tag: str, admin: User = Depends(get_current_admin_user)) -> dict:
    if not settings.allow_tag_delete:
        raise HTTPException(status_code=403, detail="未启用标签删除功能")
    client = get_registry_client()
    try:
        await client.delete_tag(name, tag)
    except RegistryNotFoundError:
        raise HTTPException(status_code=404, detail="镜像或仓库不存在")
    return {"detail": "删除已提交", "repository": name, "tag": tag}