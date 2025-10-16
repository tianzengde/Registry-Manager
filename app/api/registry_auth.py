"""Docker Registry Token Authentication API"""
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
    Docker Registry Token Authentication endpoint
    
    This endpoint is called by Docker client during authentication.
    Format: GET /token?service=registry&scope=repository:nginx:pull,push
    
    Returns a JWT token with permissions based on user's access rights.
    """
    # Try to get credentials from Basic Auth header
    auth_header = request.headers.get("Authorization", "")
    
    user = None
    if auth_header.startswith("Basic "):
        # Decode Basic Auth
        import base64
        try:
            encoded_credentials = auth_header.replace("Basic ", "")
            decoded = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded.split(":", 1)
            
            # Authenticate user
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
        # No credentials provided - this is normal for anonymous access check
        # Return error to prompt for credentials
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": 'Basic realm="Registry Realm"'},
        )
    
    # Generate registry token with permissions
    token = await registry_auth_service.generate_registry_token(
        user=user,
        scope=scope
    )
    
    # Return token in Docker Registry expected format
    return {
        "token": token,
        "access_token": token,  # Some clients expect this field
        "expires_in": 1800,  # 30 minutes in seconds
        "issued_at": None  # Optional, can be added if needed
    }

