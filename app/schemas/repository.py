"""Repository schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RepositoryBase(BaseModel):
    """Base repository schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False


class RepositoryCreate(RepositoryBase):
    """Schema for creating a repository"""
    pass


class RepositoryUpdate(BaseModel):
    """Schema for updating a repository"""
    description: Optional[str] = None
    is_public: Optional[bool] = None


class RepositoryResponse(RepositoryBase):
    """Schema for repository response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

