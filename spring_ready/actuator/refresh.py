"""
Actuator Refresh Endpoint.
Reloads configuration from Config Server at runtime.
"""

import logging
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..config.loader import ConfigServerLoader

logger = logging.getLogger(__name__)


class RefreshEndpoint:
    """
    Refresh endpoint for Spring Boot Actuator compatibility.

    Reloads configuration from Config Server and returns list of changed properties.
    This is equivalent to Spring Cloud's @RefreshScope functionality.
    """

    def __init__(self, config_loader: Optional['ConfigServerLoader'] = None):
        """
        Args:
            config_loader: ConfigServerLoader instance to refresh
        """
        self.config_loader = config_loader

    def refresh(self) -> List[str]:
        """
        Refresh configuration from Config Server.

        Returns:
            List of configuration keys that changed
        """
        if not self.config_loader:
            logger.warning("No config loader available for refresh endpoint")
            return []

        try:
            # Get current configuration snapshot
            old_config = dict(self.config_loader.config) if self.config_loader.config else {}

            # Reload configuration from Config Server
            logger.info("Refreshing configuration from Config Server...")
            self.config_loader.load_config()

            # Get new configuration
            new_config = dict(self.config_loader.config) if self.config_loader.config else {}

            # Find changed keys
            changed_keys = []

            # Check for changed values
            for key in set(old_config.keys()) | set(new_config.keys()):
                old_value = old_config.get(key)
                new_value = new_config.get(key)

                if old_value != new_value:
                    changed_keys.append(key)
                    logger.info(f"Configuration changed: {key}")

            if changed_keys:
                logger.info(f"Refreshed {len(changed_keys)} configuration properties")
            else:
                logger.info("No configuration changes detected")

            return changed_keys

        except Exception as e:
            logger.error(f"Error refreshing configuration: {e}", exc_info=True)
            return []


def create_default_refresh_endpoint(config_loader: Optional['ConfigServerLoader'] = None) -> RefreshEndpoint:
    """
    Create refresh endpoint with default configuration.

    Args:
        config_loader: ConfigServerLoader instance

    Returns:
        RefreshEndpoint instance
    """
    return RefreshEndpoint(config_loader=config_loader)
