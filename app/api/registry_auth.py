"""Docker Registry令牌认证API"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request
from app.services import AuthService, RegistryAuthService


router = APIRouter()
auth_service = AuthService()
registry_auth_service = RegistryAuthService()


@router.get("/token")
async def get_registry_token(
    request: Request,
    service: Optional[str] = None,
    scope: Optional[str] = None,
    account: Optional[str] = None
):
    """
    Docker Registry令牌认证端点
    
    此端点在身份验证期间由Docker客户端调用。
    格式: GET /token?service=registry&scope=repository:nginx:pull,push
    
    返回基于用户访问权限的JWT令牌。
    """
    # 尝试从Basic Auth头部获取凭据
    auth_header = request.headers.get("Authorization", "")
    
    user = None
    if auth_header.startswith("Basic "):
        # 解码Basic Auth
        import base64
        try:
            encoded_credentials = auth_header.replace("Basic ", "")
            decoded = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded.split(":", 1)
            
            # 验证用户
            user = await auth_service.authenticate_user(username, password)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": 'Basic realm="Registry Realm"'},
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is disabled"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": 'Basic realm="Registry Realm"'},
            )
    else:
        # 未提供凭据 - 这对于匿名访问检查是正常的
        # 返回错误以提示输入凭据
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": 'Basic realm="Registry Realm"'},
        )
    
    # 生成带权限的注册表令牌
    token = await registry_auth_service.generate_registry_token(
        user=user,
        scope=scope
    )
    
    # 以Docker Registry期望的格式返回令牌
    return {
        "token": token,
        "access_token": token,  # Some clients expect this field
        "expires_in": 1800,  # 30 minutes in seconds
        "issued_at": None  # Optional, can be added if needed
    }

