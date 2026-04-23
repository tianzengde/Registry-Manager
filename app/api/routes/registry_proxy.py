from __future__ import annotations

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.responses import StreamingResponse

from app.core.config import settings
from app.models import Repository, PullPushEvent, RepoDailyStats
from app.services import authenticate_user


router = APIRouter(prefix="/v2", tags=["registry"])

basic_security_optional = HTTPBasic(auto_error=False)


def _docker_api_headers() -> dict[str, str]:
    return {"Docker-Distribution-API-Version": "registry/2.0"}


@router.get("/", summary="Docker Registry API 入口（Basic Auth）")
async def docker_api_entry(credentials: Optional[HTTPBasicCredentials] = Depends(basic_security_optional)) -> Response:
    headers = _docker_api_headers()
    if credentials is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, headers={**headers, "WWW-Authenticate": 'Basic realm="Registry Realm"'})
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, headers={**headers, "WWW-Authenticate": 'Basic realm="Registry Realm"'})
    return Response(status_code=status.HTTP_200_OK, headers=headers)


def _extract_repo_from_path(path: str) -> Optional[str]:
    # Examples:
    #   <repo>/manifests/<ref>
    #   <repo>/blobs/<digest>
    #   <repo>/tags/list
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None
    if parts[0] == "_catalog":
        return None
    for marker in ("manifests", "blobs", "tags"):
        if marker in parts:
            idx = parts.index(marker)
            # for tags/list, repository is everything before 'tags'
            return "/".join(parts[:idx]) if idx > 0 else None
    # Fallback: treat whole path as repo (rare)
    return "/".join(parts)


def _is_write_method(method: str) -> bool:
    return method.upper() in {"PUT", "POST", "PATCH", "DELETE"}


@router.api_route("/{full_path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], summary="Registry 反向代理")
async def registry_proxy(
    full_path: str,
    request: Request,
    credentials: Optional[HTTPBasicCredentials] = Depends(basic_security_optional),
) -> Response:
    repo_name = _extract_repo_from_path(full_path)
    is_write = _is_write_method(request.method)

    # AuthZ
    user_is_admin = False
    user_authenticated = False
    if credentials is not None:
        user = await authenticate_user(credentials.username, credentials.password)
        if user:
            user_authenticated = True
            user_is_admin = bool(user.is_admin)

    if repo_name:
        repo = await Repository.get_or_create(name=repo_name)
        repo_obj = repo[0]
        if is_write:
            if not user_is_admin:
                return Response(status_code=status.HTTP_403_FORBIDDEN, headers={"WWW-Authenticate": 'Basic realm="Registry Realm"'})
        else:
            if not repo_obj.is_public and not user_authenticated:
                return Response(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": 'Basic realm="Registry Realm"'})
    else:
        # _catalog or unknown: allow; downstream endpoints will be filtered by app APIs
        pass

    # Build upstream request to internal registry service
    upstream_base = settings.registry_url.rstrip('/')
    upstream_url = f"{upstream_base}/v2/{full_path}"
    # Forward headers except Authorization (auth handled here)
    headers = {k: v for k, v in request.headers.items() if k.lower() != "authorization"}

    async with httpx.AsyncClient(timeout=settings.registry_request_timeout, verify=settings.registry_verify_ssl) as client:
        # Read body as bytes (streaming could be added later)
        body = await request.body()
        try:
            resp = await client.request(request.method, upstream_url, params=request.query_params, headers=headers, content=body)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"上游 Registry 不可用: {exc}") from exc

    # Prepare response, propagate critical headers
    forward_headers = {}
    for key in [
        "Docker-Content-Digest",
        "Content-Type",
        "Range",
        "Accept-Ranges",
        "Location",
        "Content-Length",
    ]:
        val = resp.headers.get(key)
        if val is not None:
            forward_headers[key] = val

    response = Response(content=resp.content, status_code=resp.status_code, headers=forward_headers)

    # Event recording for stats
    try:
        action = None
        tag = None
        if "/manifests/" in full_path:
            method = request.method.upper()
            if method == "GET":
                action = "pull"
            elif method in {"PUT", "POST"}:
                action = "push"
            # extract reference (tag or digest)
            try:
                segs = [p for p in full_path.split("/") if p]
                if "manifests" in segs:
                    ref_idx = segs.index("manifests") + 1
                    tag = segs[ref_idx] if ref_idx < len(segs) else None
            except Exception:
                tag = None
        elif "/blobs/" in full_path and request.method.upper() in {"PUT", "POST"}:
            action = "push"
        if action and repo_name:
            await PullPushEvent.create(repository=repo_name, tag=tag, action=action)
            # daily aggregate
            from datetime import date, datetime, timezone

            today = date.today()
            stats, _ = await RepoDailyStats.get_or_create(repository=repo_name, day=today)
            if action == "pull":
                stats.pulls += 1
            elif action == "push":
                stats.pushes += 1
            stats.last_activity_at = datetime.now(timezone.utc)
            await stats.save()
    except Exception:
        # swallow stats errors
        pass

    return response