"""Database configuration and initialization"""
import os
from pathlib import Path
from tortoise import Tortoise
from app.core.config import settings


# Ensure db directory exists
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
    """Initialize database connection"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db():
    """Close database connection"""
    await Tortoise.close_connections()

