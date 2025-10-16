"""Authentication service"""
from typing import Optional
from app.models import User
from app.core.security import verify_password, get_password_hash, create_access_token


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password"""
        user = await User.get_or_none(username=username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user
    
    @staticmethod
    async def create_user(username: str, password: str, email: Optional[str] = None, is_admin: bool = False) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(password)
        user = await User.create(
            username=username,
            password=hashed_password,
            email=email,
            is_admin=is_admin
        )
        return user
    
    @staticmethod
    async def update_password(user: User, new_password: str) -> User:
        """Update user password"""
        user.password = get_password_hash(new_password)
        await user.save()
        return user
    
    @staticmethod
    def generate_token(user: User) -> str:
        """Generate JWT token for user"""
        return create_access_token(data={"sub": user.username})
    
    @staticmethod
    async def initialize_admin_user() -> User:
        """Initialize default admin user if not exists"""
        admin = await User.get_or_none(username="admin")
        if not admin:
            admin = await AuthService.create_user(
                username="admin",
                password="admin123",
                email="admin@example.com",
                is_admin=True
            )
        return admin

