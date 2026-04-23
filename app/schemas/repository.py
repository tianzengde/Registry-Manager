from __future__ import annotations

from pydantic import BaseModel


class RepositoryRead(BaseModel):
    name: str
    is_public: bool
    tags_count: int = 0


class RepositoryUpdate(BaseModel):
    is_public: bool