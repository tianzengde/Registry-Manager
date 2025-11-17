from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings

MANIFEST_V2 = "application/vnd.docker.distribution.manifest.v2+json"
CONFIG_V1 = "application/vnd.docker.container.image.v1+json"


class RegistryClientError(RuntimeError):
    """Raised when the Docker Registry returns an unexpected response."""


class RegistryNotFoundError(RegistryClientError):
    """Raised when a repository or tag cannot be found."""


@dataclass(slots=True)
class ManifestMetadata:
    digest: str
    media_type: str
    size_bytes: int
    config_digest: str
    config_media_type: str
    architecture: str | None
    os: str | None
    created_at: datetime | None
    manifest: dict[str, Any]
    config: dict[str, Any]


class RegistryClient:
    """Lightweight async client for Docker Registry HTTP API v2."""

    def __init__(
        self,
        base_url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        verify_ssl: bool = True,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password) if username and password else None
        self.verify_ssl = verify_ssl
        self.timeout = timeout

    async def list_repositories(self, *, page_size: int = 100) -> list[str]:
        """Return all repository names available in the registry."""
        repositories: list[str] = []
        last: str | None = None

        async with self._client() as client:
            while True:
                params = {"n": page_size}
                if last:
                    params["last"] = last
                response = await client.get("/v2/_catalog", params=params)
                data = _expect_json(response)
                repos = data.get("repositories") or []
                repositories.extend(repos)

                link = response.headers.get("Link")
                if not link or 'rel="next"' not in link:
                    break
                last = _extract_last_from_link(link) or repos[-1] if repos else None
                if last is None:
                    break

        return sorted(set(repositories))

    async def list_tags(self, repository: str) -> list[str]:
        """Return all tags for a repository."""
        async with self._client() as client:
            response = await client.get(f"/v2/{repository}/tags/list")
            if response.status_code == httpx.codes.NOT_FOUND:
                raise RegistryNotFoundError(f"Repository '{repository}' not found")
            data = _expect_json(response)
        tags = data.get("tags") or []
        return sorted(tags)

    async def get_manifest(self, repository: str, reference: str) -> ManifestMetadata:
        """Fetch manifest metadata for a repository tag or digest."""
        async with self._client() as client:
            manifest_resp = await client.get(
                f"/v2/{repository}/manifests/{reference}",
                headers={"Accept": MANIFEST_V2},
            )
            if manifest_resp.status_code == httpx.codes.NOT_FOUND:
                raise RegistryNotFoundError(
                    f"Manifest '{reference}' for repository '{repository}' not found",
                )
            manifest_data = _expect_json(manifest_resp)
            manifest_digest = manifest_resp.headers.get(
                "Docker-Content-Digest",
                reference if reference.startswith("sha256:") else "",
            )

            layers = manifest_data.get("layers") or []
            size_bytes = sum(layer.get("size", 0) for layer in layers)

            config_info = manifest_data.get("config") or {}
            config_digest = config_info.get("digest")
            config_media_type = config_info.get("mediaType", "")

            config_data: dict[str, Any] = {}
            created_at: datetime | None = None
            architecture: str | None = None
            os_name: str | None = None

            if config_digest:
                config_resp = await client.get(
                    f"/v2/{repository}/blobs/{config_digest}",
                    headers={"Accept": CONFIG_V1},
                )
                config_data = _expect_json(config_resp)
                created_at = _parse_datetime(config_data.get("created"))
                architecture = config_data.get("architecture")
                os_name = config_data.get("os")

        return ManifestMetadata(
            digest=manifest_digest or reference,
            media_type=manifest_data.get("mediaType", ""),
            size_bytes=size_bytes,
            config_digest=config_digest or "",
            config_media_type=config_media_type,
            architecture=architecture,
            os=os_name,
            created_at=created_at,
            manifest=manifest_data,
            config=config_data,
        )

    async def delete_manifest(self, repository: str, digest: str) -> None:
        async with self._client() as client:
            resp = await client.delete(f"/v2/{repository}/manifests/{digest}")
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:  # pragma: no cover
                raise RegistryClientError(str(exc)) from exc

    async def delete_tag(self, repository: str, tag: str) -> None:
        # Deleting a tag requires deleting the manifest referenced by the tag.
        meta = await self.get_manifest(repository, tag)
        await self.delete_manifest(repository, meta.digest)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            auth=self.auth,
            verify=self.verify_ssl,
            timeout=self.timeout,
            headers={"Docker-Distribution-API-Version": "registry/2.0"},
        )


def get_registry_client() -> RegistryClient:
    return RegistryClient(
        settings.registry_url,
        username=settings.registry_username,
        password=settings.registry_password,
        verify_ssl=settings.registry_verify_ssl,
        timeout=settings.registry_request_timeout,
    )


def _expect_json(response: httpx.Response) -> dict[str, Any]:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:  # pragma: no cover
        raise RegistryClientError(str(exc)) from exc
    try:
        return response.json()
    except ValueError as exc:  # pragma: no cover
        raise RegistryClientError("Registry response is not JSON") from exc


def _extract_last_from_link(link_header: str) -> str | None:
    # Link format: </v2/_catalog?last=<name>&n=<size>>; rel="next"
    try:
        segment = link_header.split(";")[0]
        if segment.startswith("<") and segment.endswith(">"):
            url_part = segment[1:-1]
            query = httpx.URL(url_part).query_params
            return query.get("last")
    except Exception:  # pragma: no cover - defensive
        return None
    return None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    # Docker config uses RFC3339 format and typically ends with Z.
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None

