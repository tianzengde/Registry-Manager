"""权限管理API路由"""
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from app.models import User, Repository, Permission
from app.schemas import PermissionCreate, PermissionUpdate, PermissionResponse
from app.services import PermissionService
from app.core.security import get_current_admin_user


router = APIRouter()
permission_service = PermissionService()


@router.get("/", response_model=List[PermissionResponse])
async def list_permissions(current_user: User = Depends(get_current_admin_user)):
    """列出所有权限(仅管理员)"""
    permissions = await Permission.all()
    return permissions


@router.get("/repository/{repo_id}", response_model=List[PermissionResponse])
async def list_repository_permissions(
    repo_id: int,
    current_user: User = Depends(get_current_admin_user)
):
    """列出特定仓库的权限(仅管理员)"""
    repository = await Repository.get_or_none(id=repo_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    permissions = await permission_service.get_repository_permissions(repository)
    return permissions


@router.post("/", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    perm_data: PermissionCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """Create or update permission (admin only)"""
    user = await User.get_or_none(id=perm_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    repository = await Repository.get_or_none(id=perm_data.repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    permission = await permission_service.grant_permission(
        user=user,
        repository=repository,
        can_pull=perm_data.can_pull,
        can_push=perm_data.can_push,
        can_delete=perm_data.can_delete
    )
    
    return permission


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: int,
    perm_data: PermissionUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """Update permission (admin only)"""
    permission = await Permission.get_or_none(id=permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    permission.can_pull = perm_data.can_pull
    permission.can_push = perm_data.can_push
    permission.can_delete = perm_data.can_delete
    await permission.save()
    
    return permission


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: int,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete permission (admin only)"""
    permission = await Permission.get_or_none(id=permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    await permission.delete()

