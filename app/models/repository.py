"""仓库模型"""
from tortoise import fields
from tortoise.models import Model


class Repository(Model):
    """Docker registry仓库的仓库模型"""
    
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True, index=True)
    description = fields.TextField(null=True)
    is_public = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # 关联关系
    permissions: fields.ReverseRelation["Permission"]
    
    class Meta:
        table = "repositories"
    
    def __str__(self):
        return self.name

