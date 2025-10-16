"""Registry service for interacting with Docker Registry API"""
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings


class RegistryService:
    """Service for interacting with Docker Registry"""
    
    def __init__(self):
        self.base_url = settings.REGISTRY_URL
        self.username = settings.REGISTRY_USERNAME
        self.password = settings.REGISTRY_PASSWORD
        self.auth = (self.username, self.password) if self.username and self.password else None
        self._cache = {}  # Simple in-memory cache
    
    def clear_cache(self, pattern: str = None):
        """Clear cache entries matching pattern, or all if pattern is None"""
        if pattern is None:
            self._cache.clear()
        else:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
    
    async def list_repositories(self) -> List[str]:
        """List all repositories in the registry"""
        cache_key = "repositories:list"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2/_catalog",
                auth=self.auth,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            repos = data.get("repositories", [])
            self._cache[cache_key] = repos
            return repos
    
    async def list_tags(self, repository: str) -> List[str]:
        """List all tags for a repository"""
        cache_key = f"tags:{repository}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2/{repository}/tags/list",
                auth=self.auth,
                timeout=30.0
            )
            
            # Handle repository not found (404) gracefully
            if response.status_code == 404:
                # Repository doesn't exist, return empty list
                self._cache[cache_key] = []
                return []
            
            response.raise_for_status()
            data = response.json()
            tags = data.get("tags", [])
            self._cache[cache_key] = tags
            return tags
    
    async def get_manifest(self, repository: str, tag: str) -> tuple[Dict[str, Any], str]:
        """Get manifest for a specific image tag, returns (manifest, digest)"""
        cache_key = f"manifest:{repository}:{tag}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2/{repository}/manifests/{tag}",
                auth=self.auth,
                headers={
                    "Accept": "application/vnd.docker.distribution.manifest.v2+json"
                },
                timeout=30.0
            )
            response.raise_for_status()
            # Get digest from response header
            digest = response.headers.get("Docker-Content-Digest", "")
            manifest = response.json()
            result = (manifest, digest)
            self._cache[cache_key] = result
            return result
    
    async def get_image_config(self, repository: str, digest: str) -> Dict[str, Any]:
        """Get image configuration blob"""
        cache_key = f"config:{repository}:{digest}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2/{repository}/blobs/{digest}",
                auth=self.auth,
                timeout=30.0
            )
            response.raise_for_status()
            config = response.json()
            self._cache[cache_key] = config
            return config
    
    async def delete_manifest(self, repository: str, digest: str) -> bool:
        """Delete an image manifest by digest"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/v2/{repository}/manifests/{digest}",
                auth=self.auth,
                timeout=30.0
            )
            return response.status_code == 202
    
    async def get_image_details(self, repository: str, tag: str) -> Dict[str, Any]:
        """Get detailed information about an image"""
        try:
            manifest, manifest_digest = await self.get_manifest(repository, tag)
            
            # Extract basic info
            details = {
                "repository": repository,
                "tag": tag,
                "digest": None,
                "size": 0,
                "architecture": None,
                "os": None,
                "layers": [],
                "created": None,
                "env": [],
                "labels": {},
                "history": [],
                "cmd": None,
                "entrypoint": None,
                "workdir": None,
                "user": None,
                "exposed_ports": [],
                "volumes": [],
            }
            
            # Get config digest
            config_digest = None
            if "config" in manifest:
                config_digest = manifest["config"].get("digest")
                details["size"] = manifest["config"].get("size", 0)
            
            # Use manifest digest if available (from header)
            details["digest"] = manifest_digest or config_digest
            
            # Get config blob for more details
            if config_digest:
                try:
                    config = await self.get_image_config(repository, config_digest)
                    
                    # Basic platform info
                    details["architecture"] = config.get("architecture")
                    details["os"] = config.get("os")
                    
                    # Created time
                    if "created" in config:
                        details["created"] = config["created"]
                    
                    # Container config
                    container_config = config.get("config", {})
                    if container_config:
                        details["env"] = container_config.get("Env", [])
                        details["labels"] = container_config.get("Labels", {}) or {}
                        details["cmd"] = container_config.get("Cmd", [])
                        details["entrypoint"] = container_config.get("Entrypoint", [])
                        details["workdir"] = container_config.get("WorkingDir", "")
                        details["user"] = container_config.get("User", "")
                        
                        # Exposed ports
                        exposed_ports = container_config.get("ExposedPorts", {})
                        if exposed_ports:
                            details["exposed_ports"] = list(exposed_ports.keys())
                        
                        # Volumes
                        volumes = container_config.get("Volumes", {})
                        if volumes:
                            details["volumes"] = list(volumes.keys())
                    
                    # History (build steps)
                    if "history" in config:
                        details["history"] = [
                            {
                                "created": h.get("created", ""),
                                "created_by": h.get("created_by", ""),
                                "empty_layer": h.get("empty_layer", False),
                                "comment": h.get("comment", "")
                            }
                            for h in config["history"]
                        ]
                    
                except Exception as e:
                    print(f"Warning: Failed to get config blob: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Get layers
            if "layers" in manifest and manifest["layers"]:
                total_layer_size = sum(layer.get("size", 0) for layer in manifest["layers"])
                details["layers"] = [
                    {
                        "digest": layer.get("digest", "unknown"),
                        "size": layer.get("size", 0),
                        "mediaType": layer.get("mediaType", "unknown"),
                        "percentage": (layer.get("size", 0) / total_layer_size * 100) if total_layer_size > 0 else 0
                    }
                    for layer in manifest["layers"]
                ]
                details["size"] += total_layer_size
            
            return details
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to get image details: {str(e)}")
    
    async def check_registry_health(self) -> bool:
        """Check if registry is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v2/",
                    auth=self.auth,
                    timeout=10.0
                )
                return response.status_code == 200
        except:
            return False

