"""Permission service for access control"""
from typing import List, Optional
from app.models import User, Repository, Permission


class PermissionService:
    """Service for permission operations"""
    
    def __init__(self):
        self._cache = {}  # Cache for permission checks
    
    def _cache_key(self, user_id: int, repo_id: int, perm_type: str) -> str:
        return f"perm:{user_id}:{repo_id}:{perm_type}"
    
    def clear_cache(self, user_id: int = None):
        """Clear permission cache"""
        if user_id is None:
            self._cache.clear()
        else:
            keys = [k for k in list(self._cache.keys()) if f":{user_id}:" in k]
            for k in keys:
                del self._cache[k]
    
    async def check_permission(self, user: User, repository: Repository, permission_type: str) -> bool:
        """Check if user has permission for a repository"""
        # Admin users have all permissions
        if user.is_admin:
            return True
        
        # Check cache
        cache_key = self._cache_key(user.id, repository.id, permission_type)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Public repositories allow pull for all authenticated users
        if repository.is_public and permission_type == "pull":
            self._cache[cache_key] = True
            return True
        
        # Check specific permission
        permission = await Permission.get_or_none(user=user, repository=repository)
        if not permission:
            self._cache[cache_key] = False
            return False
        
        result = False
        if permission_type == "pull":
            result = permission.can_pull
        elif permission_type == "push":
            result = permission.can_push
        elif permission_type == "delete":
            result = permission.can_delete
        
        self._cache[cache_key] = result
        return result
    
    async def get_user_repositories(self, user: User) -> List[Repository]:
        """Get all repositories a user has access to"""
        if user.is_admin:
            # Admin can see all repositories
            return await Repository.all()
        
        # Get public repositories
        public_repos = await Repository.filter(is_public=True).all()
        
        # Get repositories with explicit permissions
        permissions = await Permission.filter(user=user).prefetch_related("repository")
        permission_repos = [p.repository for p in permissions]
        
        # Combine and deduplicate
        all_repos = list({repo.id: repo for repo in public_repos + permission_repos}.values())
        return all_repos
    
    async def grant_permission(self, user: User, repository: Repository, 
                              can_pull: bool = True, can_push: bool = False, 
                              can_delete: bool = False) -> Permission:
        """Grant permission to a user for a repository"""
        permission, created = await Permission.get_or_create(
            user=user,
            repository=repository,
            defaults={
                "can_pull": can_pull,
                "can_push": can_push,
                "can_delete": can_delete
            }
        )
        
        if not created:
            # Update existing permission
            permission.can_pull = can_pull
            permission.can_push = can_push
            permission.can_delete = can_delete
            await permission.save()
        
        return permission
    
    async def revoke_permission(self, user: User, repository: Repository) -> bool:
        """Revoke all permissions for a user on a repository"""
        permission = await Permission.get_or_none(user=user, repository=repository)
        if permission:
            await permission.delete()
            return True
        return False
    
    async def get_repository_permissions(self, repository: Repository) -> List[Permission]:
        """Get all permissions for a repository"""
        return await Permission.filter(repository=repository).prefetch_related("user")

