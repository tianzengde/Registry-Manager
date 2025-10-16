"""Repository model"""
from tortoise import fields
from tortoise.models import Model


class Repository(Model):
    """Repository model for Docker registry repositories"""
    
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True, index=True)
    description = fields.TextField(null=True)
    is_public = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Relationships
    permissions: fields.ReverseRelation["Permission"]
    
    class Meta:
        table = "repositories"
    
    def __str__(self):
        return self.name

