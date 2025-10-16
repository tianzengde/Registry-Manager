"""Docker Registry API 代理，带权限检查"""
import httpx
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request, Response, Depends
from fastapi.responses import StreamingResponse
from jose import jwt, JWTError
from app.core.config import settings
from app.models import User, Repository
from app.services import PermissionService, AuthService


router = APIRouter()
permission_service = PermissionService()
auth_service = AuthService()


async def get_user_from_token(request: Request) -> Optional[User]:
    """从 Bearer token 中提取并验证用户"""
    auth_header = request.headers.get("Authorization", "")
    
    # 调试：打印所有请求头，查看 Docker 客户端发送的内容
    print(f"[DEBUG] Request headers: {dict(request.headers)}")
    print(f"[DEBUG] Authorization header: {auth_header}")
    
    if not auth_header.startswith("Bearer "):
        print(f"[DEBUG] No Bearer token found in Authorization header")
        return None
    
    token = auth_header.replace("Bearer ", "")
    
    # 尝试解码 token
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False}  # 不验证 audience，适用于 Docker Registry tokens
        )
    except JWTError:
        return None
    
    # 从 token 中提取用户名（支持两种格式）
    # Docker Registry token 格式使用 "sub" 字段
    # 我们的 web 应用 token 也使用 "sub" 字段
    username = payload.get("sub")
    if not username:
        return None
    
    user = await User.get_or_none(username=username)
    return user if user and user.is_active else None


def parse_repository_from_path(path: str) -> Optional[str]:
    """
    从 Docker Registry API 路径中提取仓库名称
    示例:
      /v2/nginx/manifests/latest -> nginx
      /v2/myapp/blobs/sha256:xxx -> myapp
      /v2/namespace/repo/tags/list -> namespace/repo
    """
    if not path.startswith("/v2/"):
        return None
    
    # 移除 /v2/ 前缀
    path = path[4:]
    
    # 按 / 分割
    parts = path.split("/")
    
    if len(parts) == 0 or parts[0] == "" or parts[0] == "_catalog":
        return None
    
    # 对于路径如: nginx/manifests/latest 或 nginx/blobs/xxx
    # 仓库名称可以有多个部分 (namespace/repo)
    # 但通常在 /manifests/, /blobs/, /tags/ 之前结束
    
    # 查找 registry API 端点的索引
    api_endpoints = ["manifests", "blobs", "tags", "uploads"]
    repo_parts = []
    
    for i, part in enumerate(parts):
        if part in api_endpoints:
            repo_parts = parts[:i]
            break
    
    if not repo_parts:
        # 可能只是仓库名称
        repo_parts = [parts[0]]
    
    return "/".join(repo_parts) if repo_parts else None


def determine_action(method: str, path: str) -> str:
    """根据 HTTP 方法和路径确定操作类型 (pull/push/delete)"""
    if method == "GET" or method == "HEAD":
        return "pull"
    elif method == "POST" or method == "PUT" or method == "PATCH":
        return "push"
    elif method == "DELETE":
        return "delete"
    else:
        return "pull"  # 对于未知方法，默认为 pull


@router.api_route("/v2/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def registry_proxy(request: Request, path: str):
    """
    代理所有 Docker Registry API 请求，进行权限检查
    """
    full_path = f"/v2/{path}" if path else "/v2/"
    
    # 处理 OPTIONS 请求（CORS）
    if request.method == "OPTIONS":
        return Response(status_code=200)
    
    # 特殊处理 /v2/ 基础端点（registry 版本检查）
    if full_path == "/v2/" or full_path == "/v2":
        # 检查用户是否已认证
        user = await get_user_from_token(request)
        if not user:
            # 根据请求构建动态 realm URL
            host = request.headers.get("host", "127.0.0.1:3081")
            # 如果反向代理设置了 X-Forwarded-Proto，则使用它
            scheme = request.headers.get("x-forwarded-proto", "http")
            realm_url = f"{scheme}://{host}/token"
            
            # 返回 401 认证挑战
            return Response(
                status_code=401,
                headers={
                    "WWW-Authenticate": f'Bearer realm="{realm_url}",service="Docker Registry"',
                    "Docker-Distribution-Api-Version": "registry/2.0"
                },
                content=b'{"errors":[{"code":"UNAUTHORIZED","message":"authentication required"}]}'
            )
        # 已认证，返回成功
        return Response(
            status_code=200,
            headers={
                "Docker-Distribution-Api-Version": "registry/2.0",
                "Content-Type": "application/json"
            },
            content=b'{}'
        )
    
    # 目录端点 - 仅管理员
    if "_catalog" in full_path:
        user = await get_user_from_token(request)
        if not user or not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        # 管理员可以访问目录
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.REGISTRY_URL}{full_path}",
                timeout=30.0
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    
    # 提取仓库名称
    repo_name = parse_repository_from_path(full_path)
    if not repo_name:
        # 无法确定仓库，拒绝访问
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository path"
        )
    
    # 从 token 中获取用户
    user = await get_user_from_token(request)
    if not user:
        # 根据请求构建动态 realm URL
        host = request.headers.get("host", "127.0.0.1:3081")
        scheme = request.headers.get("x-forwarded-proto", "http")
        realm_url = f"{scheme}://{host}/token"
        
        return Response(
            status_code=401,
            headers={
                "WWW-Authenticate": f'Bearer realm="{realm_url}",service="Docker Registry",scope="repository:{repo_name}:pull,push"',
                "Docker-Distribution-Api-Version": "registry/2.0"
            }
        )
    
    # 确定操作类型
    action = determine_action(request.method, full_path)
    
    # 从数据库中获取或创建仓库
    repo = await Repository.get_or_none(name=repo_name)
    if not repo:
        # 仓库在数据库中不存在
        # 允许管理员通过推送创建
        if user.is_admin and action == "push":
            repo = await Repository.create(
                name=repo_name,
                description=f"Auto-created repository: {repo_name}",
                is_public=False
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
    
    # 检查权限
    has_permission = await permission_service.check_permission(user, repo, action)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No {action} permission for repository {repo_name}"
        )
    
    # 权限已授予，代理请求到实际的 registry
    async with httpx.AsyncClient() as client:
        # 准备请求
        headers = dict(request.headers)
        # 移除 host 头以避免冲突
        headers.pop("host", None)
        
        # 转发请求到 registry
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                response = await client.request(
                    method=request.method,
                    url=f"{settings.REGISTRY_URL}{full_path}",
                    content=body,
                    headers=headers,
                    timeout=300.0,
                    params=dict(request.query_params)
                )
            else:
                response = await client.request(
                    method=request.method,
                    url=f"{settings.REGISTRY_URL}{full_path}",
                    headers=headers,
                    timeout=300.0,
                    params=dict(request.query_params)
                )
            
            # 如果存在 Location 头，则重写它（用于 blob 上传）
            headers = dict(response.headers)
            if "location" in headers:
                # 将内部 registry URL 重写为外部 URL
                location = headers["location"]
                print(f"[DEBUG] Original Location: {location[:100]}...")
                print(f"[DEBUG] REGISTRY_URL: {settings.REGISTRY_URL}")
                print(f"[DEBUG] Request headers - Host: {request.headers.get('host')}, X-Forwarded-Proto: {request.headers.get('x-forwarded-proto')}")
                
                if settings.REGISTRY_URL in location:
                    # 将内部 URL 替换为外部 URL
                    host = request.headers.get("host", "127.0.0.1:3081")
                    scheme = request.headers.get("x-forwarded-proto", "http")
                    external_base = f"{scheme}://{host}"
                    location = location.replace(settings.REGISTRY_URL, external_base)
                    headers["location"] = location
                    print(f"[DEBUG] Scheme: {scheme}, Rewritten Location: {location[:100]}...")
            
            # 返回响应
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=headers
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to registry: {str(e)}"
            )

