"""
Actuator Caches Endpoint.
Provides access to application caches.
"""

from typing import Dict, Any, Optional, List


class CachesEndpoint:
    """
    Caches endpoint for Spring Boot Actuator compatibility.

    Provides access to application caches.
    Currently returns empty structure as no cache manager is configured by default.
    Can be extended to integrate with Redis, Memcached, or in-memory caches.
    """

    def __init__(self):
        """Initialize caches endpoint"""
        self.cache_managers: Dict[str, Dict[str, Any]] = {}

    def get_caches(self) -> Dict[str, Any]:
        """
        Get all caches.

        Returns:
            Dictionary with cache managers and caches
        """
        caches = {}

        for manager_name, manager_info in self.cache_managers.items():
            for cache_name in manager_info.get("caches", []):
                caches[cache_name] = {
                    "target": f"{manager_name}::{cache_name}",
                    "cacheManager": manager_name
                }

        return {
            "cacheManagers": self.cache_managers,
            "caches": caches
        }

    def get_cache(self, cache_name: str, cache_manager: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific cache.

        Args:
            cache_name: Cache name
            cache_manager: Optional cache manager name

        Returns:
            Cache details or None if not found
        """
        for manager_name, manager_info in self.cache_managers.items():
            if cache_manager and manager_name != cache_manager:
                continue

            if cache_name in manager_info.get("caches", []):
                return {
                    "target": f"{manager_name}::{cache_name}",
                    "name": cache_name,
                    "cacheManager": manager_name
                }

        return None

    def evict_cache(self, cache_name: str, cache_manager: Optional[str] = None) -> bool:
        """
        Evict a specific cache.

        Args:
            cache_name: Cache name
            cache_manager: Optional cache manager name

        Returns:
            True if cache was evicted, False otherwise
        """
        # Placeholder - actual eviction would depend on cache implementation
        return self.get_cache(cache_name, cache_manager) is not None

    def evict_all_caches(self) -> bool:
        """
        Evict all caches.

        Returns:
            True if successful
        """
        # Placeholder - actual eviction would depend on cache implementation
        return True

    def add_cache_manager(self, name: str, caches: List[str]) -> None:
        """
        Register a cache manager.

        Args:
            name: Cache manager name
            caches: List of cache names
        """
        self.cache_managers[name] = {
            "caches": caches
        }


def create_default_caches_endpoint() -> CachesEndpoint:
    """
    Create caches endpoint with default configuration.

    Returns:
        CachesEndpoint instance
    """
    return CachesEndpoint()
