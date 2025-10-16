"""Docker Registry API Proxy with Permission Check"""
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
    """Extract and validate user from Bearer token"""
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    
    # Try to decode the token
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False}  # Don't verify audience for Docker Registry tokens
        )
    except JWTError:
        return None
    
    # Extract username from token (supports both formats)
    # Docker Registry token format uses "sub" field
    # Our web app token also uses "sub" field
    username = payload.get("sub")
    if not username:
        return None
    
    user = await User.get_or_none(username=username)
    return user if user and user.is_active else None


def parse_repository_from_path(path: str) -> Optional[str]:
    """
    Extract repository name from Docker Registry API path
    Examples:
      /v2/nginx/manifests/latest -> nginx
      /v2/myapp/blobs/sha256:xxx -> myapp
      /v2/namespace/repo/tags/list -> namespace/repo
    """
    if not path.startswith("/v2/"):
        return None
    
    # Remove /v2/ prefix
    path = path[4:]
    
    # Split by /
    parts = path.split("/")
    
    if len(parts) == 0 or parts[0] == "" or parts[0] == "_catalog":
        return None
    
    # For paths like: nginx/manifests/latest or nginx/blobs/xxx
    # Repository name can have multiple parts (namespace/repo)
    # But typically ends before /manifests/, /blobs/, /tags/
    
    # Find the index of the registry API endpoint
    api_endpoints = ["manifests", "blobs", "tags", "uploads"]
    repo_parts = []
    
    for i, part in enumerate(parts):
        if part in api_endpoints:
            repo_parts = parts[:i]
            break
    
    if not repo_parts:
        # Maybe it's just the repository name
        repo_parts = [parts[0]]
    
    return "/".join(repo_parts) if repo_parts else None


def determine_action(method: str, path: str) -> str:
    """Determine the action (pull/push/delete) based on HTTP method and path"""
    if method == "GET" or method == "HEAD":
        return "pull"
    elif method == "POST" or method == "PUT" or method == "PATCH":
        return "push"
    elif method == "DELETE":
        return "delete"
    else:
        return "pull"  # Default to pull for unknown methods


@router.api_route("/v2/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def registry_proxy(request: Request, path: str):
    """
    Proxy all Docker Registry API requests through permission checking
    """
    full_path = f"/v2/{path}" if path else "/v2/"
    
    # Handle OPTIONS for CORS
    if request.method == "OPTIONS":
        return Response(status_code=200)
    
    # Special handling for /v2/ base endpoint (registry version check)
    if full_path == "/v2/" or full_path == "/v2":
        # Check if user is authenticated
        user = await get_user_from_token(request)
        if not user:
            # Build dynamic realm URL based on request
            host = request.headers.get("host", "127.0.0.1:3081")
            # Use X-Forwarded-Proto if set by reverse proxy
            scheme = request.headers.get("x-forwarded-proto", "http")
            realm_url = f"{scheme}://{host}/token"
            
            # Return 401 with authentication challenge
            return Response(
                status_code=401,
                headers={
                    "WWW-Authenticate": f'Bearer realm="{realm_url}",service="Docker Registry"',
                    "Docker-Distribution-Api-Version": "registry/2.0"
                },
                content=b'{"errors":[{"code":"UNAUTHORIZED","message":"authentication required"}]}'
            )
        # Authenticated, return success
        return Response(
            status_code=200,
            headers={
                "Docker-Distribution-Api-Version": "registry/2.0",
                "Content-Type": "application/json"
            },
            content=b'{}'
        )
    
    # Catalog endpoint - admin only
    if "_catalog" in full_path:
        user = await get_user_from_token(request)
        if not user or not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        # Admin can access catalog
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
    
    # Extract repository name
    repo_name = parse_repository_from_path(full_path)
    if not repo_name:
        # Can't determine repository, deny access
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository path"
        )
    
    # Get user from token
    user = await get_user_from_token(request)
    if not user:
        # Build dynamic realm URL based on request
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
    
    # Determine action
    action = determine_action(request.method, full_path)
    
    # Get or create repository in database
    repo = await Repository.get_or_none(name=repo_name)
    if not repo:
        # Repository doesn't exist in DB
        # Allow admin to create it via push
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
    
    # Check permission
    has_permission = await permission_service.check_permission(user, repo, action)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No {action} permission for repository {repo_name}"
        )
    
    # Permission granted, proxy request to actual registry
    async with httpx.AsyncClient() as client:
        # Prepare request
        headers = dict(request.headers)
        # Remove host header to avoid conflicts
        headers.pop("host", None)
        
        # Forward request to registry
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
            
            # Rewrite Location header if present (for blob uploads)
            headers = dict(response.headers)
            if "location" in headers:
                # Rewrite internal registry URL to external URL
                location = headers["location"]
                print(f"[DEBUG] Original Location: {location[:100]}...")
                print(f"[DEBUG] REGISTRY_URL: {settings.REGISTRY_URL}")
                print(f"[DEBUG] Request headers - Host: {request.headers.get('host')}, X-Forwarded-Proto: {request.headers.get('x-forwarded-proto')}")
                
                if settings.REGISTRY_URL in location:
                    # Replace internal URL with external URL
                    host = request.headers.get("host", "127.0.0.1:3081")
                    scheme = request.headers.get("x-forwarded-proto", "http")
                    external_base = f"{scheme}://{host}"
                    location = location.replace(settings.REGISTRY_URL, external_base)
                    headers["location"] = location
                    print(f"[DEBUG] Scheme: {scheme}, Rewritten Location: {location[:100]}...")
            
            # Return response
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

