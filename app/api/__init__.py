"""API routes"""
from fastapi import APIRouter
from app.api import auth, users, repositories, images, permissions, pages


api_router = APIRouter()

# API routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
api_router.include_router(images.router, prefix="/images", tags=["Images"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])

# Page routes (HTML)
page_router = APIRouter()
page_router.include_router(pages.router, tags=["Pages"])

