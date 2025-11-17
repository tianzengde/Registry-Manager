from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure environment variables from .env files are loaded early.
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    project_name: str = "Registry Manager"
    debug: bool = False
    secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    # Database
    database_url: str = "sqlite://db/registry_manager.db"

    # Registry connectivity
    registry_url: str = "http://registry-manager-app:8000"  # proxy through app
    registry_username: str | None = None
    registry_password: str | None = None
    registry_verify_ssl: bool = True
    registry_request_timeout: float = 10.0

    # Admin
    admin_initial_password: str = "admin"
    allow_tag_delete: bool = False

    # Frontend
    static_dir: Path = Path("frontend")
    static_url: str = "/"

    @property
    def tortoise_modules(self) -> dict:
        return {"models": ["app.models"]}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

