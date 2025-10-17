"""HTML页面路由"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.models import User
from app.core.security import get_current_user


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """重定向到登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """仪表板页面 - 需要通过前端进行身份验证"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/repositories", response_class=HTMLResponse)
async def repositories_page(request: Request):
    """Repositories page"""
    return templates.TemplateResponse("repositories.html", {"request": request})


@router.get("/repository/{repo_name:path}", response_class=HTMLResponse)
async def repository_detail_page(request: Request, repo_name: str):
    """Repository detail page"""
    return templates.TemplateResponse("repository_detail.html", {"request": request, "repo_name": repo_name})


@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """Users management page (admin only)"""
    return templates.TemplateResponse("users.html", {"request": request})


@router.get("/permissions", response_class=HTMLResponse)
async def permissions_page(request: Request):
    """Permissions management page (admin only)"""
    return templates.TemplateResponse("permissions.html", {"request": request})

