"""Authentication API routes"""
from fastapi import APIRouter, HTTPException, status
from app.schemas import UserLogin, Token
from app.services import AuthService


router = APIRouter()
auth_service = AuthService()


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and get access token"""
    user = await auth_service.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = auth_service.generate_token(user)
    return {"access_token": access_token, "token_type": "bearer"}

