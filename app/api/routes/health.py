from fastapi import APIRouter

router = APIRouter(prefix="/health")


@router.get("/", summary="Health check")
async def health_check() -> dict:
    """Return application health status."""

    return {"status": "ok"}

