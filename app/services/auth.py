"""身份验证服务"""
from typing import Optional
from app.models import User
from app.core.security import verify_password, get_password_hash, create_access_token


class AuthService:
    """身份验证操作服务"""
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[User]:
        """通过用户名和密码验证用户"""
        user = await User.get_or_none(username=username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user
    
    @staticmethod
    async def create_user(username: str, password: str, email: Optional[str] = None, is_admin: bool = False) -> User:
        """创建新用户"""
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
        """更新用户密码"""
        user.password = get_password_hash(new_password)
        await user.save()
        return user
    
    @staticmethod
    def generate_token(user: User) -> str:
        """为用户生成JWT令牌"""
        return create_access_token(data={"sub": user.username})
    
    @staticmethod
    async def initialize_admin_user() -> User:
        """如果不存在则初始化默认管理员用户"""
        admin = await User.get_or_none(username="admin")
        if not admin:
            admin = await AuthService.create_user(
                username="admin",
                password="admin123",
                email="admin@example.com",
                is_admin=True
            )
        return admin

