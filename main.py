"""Main FastAPI application"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db, close_db
from app.core.config import settings
from app.api import api_router, page_router
from app.utils.init_data import initialize_default_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print(">> Starting Docker Registry Manager...")
    await init_db()
    print(">> Database initialized")
    
    await initialize_default_data()
    print(">> Default data initialized")
    
    print(f">> Server running on http://{settings.HOST}:{settings.PORT}")
    print(f">> Registry URL: {settings.REGISTRY_URL}")
    
    yield
    
    # Shutdown
    await close_db()
    print(">> Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(page_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
