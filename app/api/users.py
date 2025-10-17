"""用户管理API路由"""
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from app.models import User
from app.schemas import UserCreate, UserUpdate, UserResponse
from app.services import AuthService
from app.core.security import get_current_user, get_current_admin_user


router = APIRouter()
auth_service = AuthService()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.get("/", response_model=List[UserResponse])
async def list_users(current_user: User = Depends(get_current_admin_user)):
    """列出所有用户(仅管理员)"""
    users = await User.all()
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, current_user: User = Depends(get_current_admin_user)):
    """创建新用户(仅管理员)"""
    existing_user = await User.get_or_none(username=user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    user = await auth_service.create_user(
        username=user_data.username,
        password=user_data.password,
        email=user_data.email
    )
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: User = Depends(get_current_admin_user)):
    """Get user by ID (admin only)"""
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """Update user (admin only)"""
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.password is not None:
        await auth_service.update_password(user, user_data.password)
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    await user.save()
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: User = Depends(get_current_admin_user)):
    """Delete user (admin only)"""
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.username == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin user"
        )
    
    await user.delete()

