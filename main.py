"""主FastAPI应用程序"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db, close_db
from app.core.config import settings
from app.api import api_router, page_router
from app.api.registry_auth import router as registry_auth_router
from app.api.registry_proxy import router as registry_proxy_router
from app.utils.init_data import initialize_default_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理器"""
    # 启动
    print(">> 正在启动Docker Registry管理器...")
    await init_db()
    print(">> 数据库已初始化")
    
    await initialize_default_data()
    print(">> 默认数据已初始化")
    
    print(f">> 服务器运行在 http://{settings.HOST}:{settings.PORT}")
    print(f">> Registry URL: {settings.REGISTRY_URL}")
    
    yield
    
    # 关闭
    await close_db()
    print(">> 数据库连接已关闭")


# 创建FastAPI应用程序
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 包含路由器
app.include_router(registry_auth_router)  # 根级别的Registry令牌认证
app.include_router(registry_proxy_router)  # 带权限检查的Registry API代理
app.include_router(api_router, prefix="/api")
app.include_router(page_router)


@app.get("/api/health")
async def health_check():
    """健康检查端点"""
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
