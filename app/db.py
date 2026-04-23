from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from pathlib import Path

from app.core.config import settings


def _ensure_sqlite_parent_dir(db_url: str) -> None:
    """Create parent directory for sqlite db file if needed."""

    if not db_url.startswith("sqlite://"):
        return

    db_path_part = db_url.removeprefix("sqlite://")
    if not db_path_part or db_path_part == ":memory:":
        return

    db_path = Path(db_path_part)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)


def init_db(app: FastAPI) -> None:
    """Register Tortoise ORM with the FastAPI application."""

    _ensure_sqlite_parent_dir(settings.database_url)

    register_tortoise(
        app,
        db_url=settings.database_url,
        modules=settings.tortoise_modules,
        generate_schemas=True,
        add_exception_handlers=True,
    )

