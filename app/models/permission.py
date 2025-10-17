"""权限模型"""
from tortoise import fields
from tortoise.models import Model


class PermissionType(str):
    """权限类型"""
    PULL = "pull"
    PUSH = "push"
    DELETE = "delete"


class Permission(Model):
    """用于仓库访问控制的权限模型"""
    
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="permissions", on_delete=fields.CASCADE)
    repository = fields.ForeignKeyField("models.Repository", related_name="permissions", on_delete=fields.CASCADE)
    can_pull = fields.BooleanField(default=True)
    can_push = fields.BooleanField(default=False)
    can_delete = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "permissions"
        unique_together = (("user", "repository"),)
    
    def __str__(self):
        return f"{self.user.username} -> {self.repository.name}"

