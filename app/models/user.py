"""用户模型"""
from tortoise import fields
from tortoise.models import Model


class User(Model):
    """用于身份验证和授权的用户模型"""
    
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, index=True)
    password = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, null=True)
    is_active = fields.BooleanField(default=True)
    is_admin = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # 关联关系
    permissions: fields.ReverseRelation["Permission"]
    
    class Meta:
        table = "users"
    
    def __str__(self):
        return self.username

