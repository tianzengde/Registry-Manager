"""Application configuration"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Docker Registry Frontend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite://db/db.sqlite3"
    
    # Docker Registry
    REGISTRY_URL: str = "http://127.0.0.1:5000"
    REGISTRY_USERNAME: str = "admin"
    REGISTRY_PASSWORD: str = "123456"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

