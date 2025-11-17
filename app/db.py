from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.core.config import settings


def init_db(app: FastAPI) -> None:
    """Register Tortoise ORM with the FastAPI application."""

    register_tortoise(
        app,
        db_url=settings.database_url,
        modules=settings.tortoise_modules,
        generate_schemas=True,
        add_exception_handlers=True,
    )

