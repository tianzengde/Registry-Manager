"""
Service layer for domain logic.
"""

from .user_service import create_default_admin, authenticate_user, get_user_by_username, update_password, mark_user_login
from .registry_client import (
    RegistryClient,
    RegistryClientError,
    RegistryNotFoundError,
    ManifestMetadata,
    get_registry_client,
)

__all__ = [
    "create_default_admin",
    "authenticate_user",
    "get_user_by_username",
    "update_password",
    "mark_user_login",
    "RegistryClient",
    "RegistryClientError",
    "RegistryNotFoundError",
    "ManifestMetadata",
    "get_registry_client",
]

