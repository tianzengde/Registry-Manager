"""Image schemas for Docker Registry API responses"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ImageTagResponse(BaseModel):
    """Schema for image tag response"""
    name: str
    tags: List[str]


class ImageManifest(BaseModel):
    """Schema for image manifest"""
    schemaVersion: int
    mediaType: str
    config: Dict[str, Any]
    layers: List[Dict[str, Any]]
    architecture: Optional[str] = None
    os: Optional[str] = None


class ImageResponse(BaseModel):
    """Schema for image response"""
    repository: str
    tag: str
    digest: Optional[str] = None
    size: Optional[int] = None
    created: Optional[str] = None
    architecture: Optional[str] = None
    os: Optional[str] = None

