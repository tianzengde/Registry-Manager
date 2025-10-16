"""Docker Registry Token Authentication Service"""
from datetime import datetime, timedelta
from typing import List, Optional
from jose import jwt
from app.core.config import settings
from app.models import User, Repository
from app.services.permission import PermissionService


class RegistryAuthService:
    """Service for Docker Registry Token Authentication"""
    
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
        Generate Docker Registry JWT token
        
        Scope format: repository:namespace/repo:pull,push
        """
        # Parse scope to determine permissions
        access_list = []
        
        if scope:
            # Parse scope: "repository:nginx:pull,push"
            parts = scope.split(":")
            if len(parts) == 3:
                resource_type, resource_name, actions = parts
                requested_actions = actions.split(",")
                
                # Get repository from database
                repo = await Repository.get_or_none(name=resource_name)
                
                if repo:
                    # Check permissions for each action
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
                    
                    # Add to access list if any actions granted
                    if granted_actions:
                        access_list.append({
                            "type": resource_type,
                            "name": resource_name,
                            "actions": granted_actions
                        })
                else:
                    # Repository doesn't exist in DB yet
                    # Allow push for admin users (to create new repos)
                    if user.is_admin and "push" in requested_actions:
                        access_list.append({
                            "type": resource_type,
                            "name": resource_name,
                            "actions": ["pull", "push"] if user.is_admin else []
                        })
        
        # Generate JWT token
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
        
        # Add access list if any permissions granted
        if access_list:
            token_data["access"] = access_list
        
        # Sign token
        token = jwt.encode(
            token_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return token
    
    def parse_scope(self, scope: str) -> dict:
        """Parse Docker Registry scope string"""
        parts = scope.split(":")
        if len(parts) != 3:
            return {}
        
        return {
            "type": parts[0],
            "name": parts[1],
            "actions": parts[2].split(",")
        }

