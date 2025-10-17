"""仓库管理API路由"""
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from app.models import User, Repository
from app.schemas import RepositoryCreate, RepositoryUpdate, RepositoryResponse
from app.services import PermissionService
from app.core.security import get_current_user, get_current_admin_user


router = APIRouter()
permission_service = PermissionService()


@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(current_user: User = Depends(get_current_user)):
    """列出当前用户可访问的仓库"""
    repositories = await permission_service.get_user_repositories(current_user)
    return repositories


@router.post("/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repo_data: RepositoryCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """创建新仓库(仅管理员)"""
    existing_repo = await Repository.get_or_none(name=repo_data.name)
    if existing_repo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository already exists"
        )
    
    repository = await Repository.create(
        name=repo_data.name,
        description=repo_data.description,
        is_public=repo_data.is_public
    )
    return repository


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: int, current_user: User = Depends(get_current_user)):
    """Get repository by ID"""
    repository = await Repository.get_or_none(id=repo_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Check access permission
    has_access = await permission_service.check_permission(current_user, repository, "pull")
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this repository"
        )
    
    return repository


@router.put("/{repo_id}", response_model=RepositoryResponse)
async def update_repository(
    repo_id: int,
    repo_data: RepositoryUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """Update repository (admin only)"""
    repository = await Repository.get_or_none(id=repo_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    if repo_data.description is not None:
        repository.description = repo_data.description
    if repo_data.is_public is not None:
        repository.is_public = repo_data.is_public
    
    await repository.save()
    return repository


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(repo_id: int, current_user: User = Depends(get_current_admin_user)):
    """Delete repository (admin only)"""
    repository = await Repository.get_or_none(id=repo_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    await repository.delete()

