"""镜像管理API路由"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.models import User, Repository
from app.schemas import ImageTagResponse, ImageResponse
from app.services import RegistryService, PermissionService
from app.core.security import get_current_user, get_current_admin_user


router = APIRouter()
registry_service = RegistryService()
permission_service = PermissionService()


@router.post("/cache/clear")
async def clear_cache(current_user: User = Depends(get_current_admin_user)):
    """清除注册表服务缓存(仅管理员)"""
    registry_service.clear_cache()
    return {"message": "缓存清除成功"}


@router.get("/catalog", response_model=List[str])
async def list_catalog(current_user: User = Depends(get_current_user)):
    """列出注册表中所有可用的镜像"""
    try:
        repos = await registry_service.list_repositories()
        
        # 根据用户权限过滤仓库
        accessible_repos = []
        for repo_name in repos:
            repo = await Repository.get_or_none(name=repo_name)
            if repo:
                has_access = await permission_service.check_permission(current_user, repo, "pull")
                if has_access:
                    accessible_repos.append(repo_name)
            else:
                # Repository not in database, accessible only to admins
                if current_user.is_admin:
                    accessible_repos.append(repo_name)
        
        return accessible_repos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list catalog: {str(e)}"
        )


@router.get("/{repository:path}/tags", response_model=ImageTagResponse)
async def list_image_tags(repository: str, current_user: User = Depends(get_current_user)):
    """List all tags for a repository"""
    # Admin can access all, skip permission check
    if not current_user.is_admin:
        # Check repository access
        repo = await Repository.get_or_none(name=repository)
        if repo:
            has_access = await permission_service.check_permission(current_user, repo, "pull")
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No access to this repository"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this repository"
            )
    
    try:
        tags = await registry_service.list_tags(repository)
        return {"name": repository, "tags": tags}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tags: {str(e)}"
        )


@router.get("/{repository:path}/{tag}/details", response_model=ImageResponse)
async def get_image_details(
    repository: str,
    tag: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about an image"""
    # Admin can access all, skip permission check
    if not current_user.is_admin:
        # Check repository access
        repo = await Repository.get_or_none(name=repository)
        if repo:
            has_access = await permission_service.check_permission(current_user, repo, "pull")
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No access to this repository"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this repository"
            )
    
    try:
        details = await registry_service.get_image_details(repository, tag)
        return details
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get image details: {str(e)}"
        )


@router.get("/{repository:path}/{tag}/pull-command")
async def get_pull_command(
    repository: str,
    tag: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get docker pull command with current host"""
    # Admin can access all, skip permission check for faster response
    if not current_user.is_admin:
        # Check repository access
        repo = await Repository.get_or_none(name=repository)
        if repo:
            has_access = await permission_service.check_permission(current_user, repo, "pull")
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No access to this repository"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this repository"
            )
    
    # Get host from request
    host = request.headers.get("host", "localhost")
    pull_command = f"docker pull {host}/{repository}:{tag}"
    
    return {"command": pull_command}


@router.delete("/{repository:path}/{tag}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    repository: str,
    tag: str,
    current_user: User = Depends(get_current_admin_user)
):
    """删除镜像(仅管理员)"""
    try:
        # 获取清单以获取摘要
        manifest, digest = await registry_service.get_manifest(repository, tag)
        
        if not digest:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取镜像摘要"
            )
        
        # 删除镜像清单
        success = await registry_service.delete_manifest(repository, digest)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除镜像失败"
            )
        
        # 清除相关缓存
        registry_service.clear_cache(f"manifest:{repository}:{tag}")
        registry_service.clear_cache(f"tags:{repository}")
        registry_service.clear_cache("repositories:list")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除镜像失败: {str(e)}"
        )

