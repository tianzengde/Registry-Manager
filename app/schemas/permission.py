"""Permission schemas"""
from datetime import datetime
from pydantic import BaseModel


class PermissionBase(BaseModel):
    """Base permission schema"""
    can_pull: bool = True
    can_push: bool = False
    can_delete: bool = False


class PermissionCreate(PermissionBase):
    """Schema for creating a permission"""
    user_id: int
    repository_id: int


class PermissionUpdate(PermissionBase):
    """Schema for updating a permission"""
    pass


class PermissionResponse(PermissionBase):
    """Schema for permission response"""
    id: int
    user_id: int
    repository_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

