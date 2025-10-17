"""Docker Registry令牌认证服务"""
from datetime import datetime, timedelta
from typing import List, Optional
from jose import jwt
from app.core.config import settings
from app.models import User, Repository
from app.services.permission import PermissionService


class RegistryAuthService:
    """Docker Registry令牌认证服务"""
    
    def __init__(self):
        self.permission_service = PermissionService()
        self.issuer = "Docker Registry Frontend"
        self.service = "Docker Registry"
    
    async def generate_registry_token(
        self,
        user: User,
        scope: Optional[str] = None
    ) -> str:
        """
        生成Docker Registry JWT令牌
        
        作用域格式: repository:namespace/repo:pull,push
        """
        # 解析作用域以确定权限
        access_list = []
        
        if scope:
            # 解析作用域: "repository:nginx:pull,push"
            parts = scope.split(":")
            if len(parts) == 3:
                resource_type, resource_name, actions = parts
                requested_actions = actions.split(",")
                
                # 从数据库获取仓库
                repo = await Repository.get_or_none(name=resource_name)
                
                if repo:
                    # 检查每个操作的权限
                    granted_actions = []
                    
                    for action in requested_actions:
                        if action == "pull":
                            has_perm = await self.permission_service.check_permission(
                                user, repo, "pull"
                            )
                            if has_perm:
                                granted_actions.append("pull")
                        
                        elif action == "push":
                            has_perm = await self.permission_service.check_permission(
                                user, repo, "push"
                            )
                            if has_perm:
                                granted_actions.append("push")
                        
                        elif action in ["delete", "*"]:
                            has_perm = await self.permission_service.check_permission(
                                user, repo, "delete"
                            )
                            if has_perm:
                                granted_actions.append(action)
                    
                    # 如果授予了任何操作，则添加到访问列表
                    if granted_actions:
                        access_list.append({
                            "type": resource_type,
                            "name": resource_name,
                            "actions": granted_actions
                        })
                else:
                    # 仓库在数据库中尚不存在
                    # 允许管理员用户推送(以创建新仓库)
                    if user.is_admin and "push" in requested_actions:
                        access_list.append({
                            "type": resource_type,
                            "name": resource_name,
                            "actions": ["pull", "push"] if user.is_admin else []
                        })
        
        # 生成JWT令牌
        now = datetime.utcnow()
        expire = now + timedelta(minutes=30)  # Token valid for 30 minutes
        
        token_data = {
            "iss": self.issuer,  # Issuer
            "sub": user.username,  # Subject (username)
            "aud": self.service,  # Audience
            "exp": expire,  # Expiration time
            "nbf": now,  # Not before
            "iat": now,  # Issued at
            "jti": f"{user.id}-{int(now.timestamp())}",  # JWT ID
        }
        
        # 如果授予了任何权限，则添加访问列表
        if access_list:
            token_data["access"] = access_list
        
        # 签名令牌
        token = jwt.encode(
            token_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return token
    
    def parse_scope(self, scope: str) -> dict:
        """解析Docker Registry作用域字符串"""
        parts = scope.split(":")
        if len(parts) != 3:
            return {}
        
        return {
            "type": parts[0],
            "name": parts[1],
            "actions": parts[2].split(",")
        }

