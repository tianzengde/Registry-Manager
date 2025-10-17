"""数据库配置和初始化"""
import os
from pathlib import Path
from tortoise import Tortoise
from app.core.config import settings


# 确保数据库目录存在
DB_DIR = Path("db")
DB_DIR.mkdir(exist_ok=True)

TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL
    },
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}


async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db():
    """关闭数据库连接"""
    await Tortoise.close_connections()

