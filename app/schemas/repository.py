from __future__ import annotations

from pydantic import BaseModel


class RepositoryRead(BaseModel):
    name: str
    is_public: bool


class RepositoryUpdate(BaseModel):
    is_public: bool