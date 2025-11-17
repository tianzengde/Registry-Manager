from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.api.routes import registry_proxy
from app.core.config import settings
from app.db import init_db
from app.services import create_default_admin
from app.models import Repository


def create_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, debug=settings.debug)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 首先注册 API 路由，确保 API 请求不被 SPA 路由捕获
    app.include_router(api_router, prefix="/api")
    # Mount Docker Registry proxy at root so docker client can access /v2
    app.include_router(registry_proxy.router)

    static_dir = settings.static_dir
    if static_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=static_dir / "assets"),
            name="assets",
        )

        @app.get("/", include_in_schema=False)
        async def serve_index():
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return JSONResponse({"detail": "index.html not found"}, status_code=404)

        @app.get("/login", include_in_schema=False)
        async def serve_login():
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return JSONResponse({"detail": "index.html not found"}, status_code=404)

        @app.get("/guest", include_in_schema=False)
        async def serve_guest():
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return JSONResponse({"detail": "index.html not found"}, status_code=404)

        @app.get("/repos", include_in_schema=False)
        async def serve_repos():
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return JSONResponse({"detail": "index.html not found"}, status_code=404)

        @app.get("/dashboard", include_in_schema=False)
        async def serve_dashboard():
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return JSONResponse({"detail": "index.html not found"}, status_code=404)

        @app.get("/settings", include_in_schema=False)
        async def serve_settings():
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return JSONResponse({"detail": "index.html not found"}, status_code=404)

        # 处理所有其他前端路由 - SPA 路由
        @app.get("/{path:path}", include_in_schema=False)
        async def serve_spa_routes(path: str):
            # 排除 API 路由和静态资源
            if path.startswith("api/") or '.' in path:
                return JSONResponse({"detail": "Not Found"}, status_code=404)
            # 处理所有其他前端路由
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return JSONResponse({"detail": "index.html not found"}, status_code=404)

    init_db(app)

    @app.on_event("startup")
    async def ensure_default_admin() -> None:
        await create_default_admin()

    @app.on_event("startup")
    async def ensure_public_namespace() -> None:
        await Repository.get_or_create(name="public", defaults={"is_public": True})

    return app


app = create_app()

