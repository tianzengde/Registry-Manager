from fastapi import APIRouter

from app.api.routes import health, auth, repositories, images, registry_proxy, dashboard, logs

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(repositories.router)
api_router.include_router(images.router)
api_router.include_router(registry_proxy.router)
api_router.include_router(dashboard.router)
api_router.include_router(logs.router)

__all__ = ["api_router"]