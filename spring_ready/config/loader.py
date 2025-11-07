"""
Config Server integration with Eureka discovery.
Extends the existing spring-config-client to support Eureka-based discovery.
"""

import os
import logging
from typing import Optional, List
from urllib.parse import urljoin

from ..exceptions import ConfigServerError
from ..retry import retry_with_backoff, RetryConfig
from ..eureka.discovery import ServiceDiscovery

logger = logging.getLogger(__name__)

# Try to import the existing config client
try:
    from spring_config_client.client import SpringConfigClient as BaseConfigClient

    HAS_CONFIG_CLIENT = True
except ImportError:
    HAS_CONFIG_CLIENT = False
    logger.warning("spring-config-client-python not installed. Config loading will be limited.")


class ConfigServerLoader:
    """
    Config Server loader with Eureka service discovery support.

    Supports two modes:
    1. Direct URL: Use spring.cloud.config.uri
    2. Eureka Discovery: Discover config server from Eureka using service-id
    """

    def __init__(
            self,
            app_name: str,
            profile: str = "default",
            config_server_url: Optional[str] = None,
            config_server_service_id: Optional[str] = None,
            service_discovery: Optional[ServiceDiscovery] = None,
            username: Optional[str] = None,
            password: Optional[str] = None,
            retry_config: Optional[RetryConfig] = None,
            fail_fast: bool = True
    ):
        """
        Args:
            app_name: Application name
            profile: Active profile (dev, prod, etc.)
            config_server_url: Direct Config Server URL (if not using discovery)
            config_server_service_id: Config Server service ID in Eureka (default: CONFIG-SERVER)
            service_discovery: ServiceDiscovery instance for finding config server
            username: Basic auth username
            password: Basic auth password
            retry_config: Retry configuration
            fail_fast: If True, fail immediately if config loading fails
        """
        self.app_name = app_name
        self.profile = profile
        self.config_server_url = config_server_url
        self.config_server_service_id = config_server_service_id or "CONFIG-SERVER"
        self.service_discovery = service_discovery
        self.username = username
        self.password = password
        self.retry_config = retry_config or RetryConfig()
        self.fail_fast = fail_fast
        self.config: dict = {}  # Store loaded configuration for refresh endpoint

        if not HAS_CONFIG_CLIENT:
            logger.warning(
                "spring-config-client-python not installed. "
                "Install it with: pip install spring-config-client-python"
            )

    def _discover_config_server(self) -> str:
        """
        Discover Config Server URL from Eureka.

        Returns:
            Config Server base URL

        Raises:
            ConfigServerError if discovery fails
        """
        if not self.service_discovery:
            raise ConfigServerError(
                "Service discovery not available. "
                "Either provide config_server_url or enable Eureka discovery."
            )

        try:
            logger.info(f"Discovering Config Server via Eureka (service-id: {self.config_server_service_id})")
            url = self.service_discovery.get_service_url(self.config_server_service_id)
            logger.info(f"Discovered Config Server at: {url}")
            return url

        except Exception as e:
            raise ConfigServerError(
                f"Failed to discover Config Server from Eureka: {e}"
            ) from e

    def _get_config_server_url(self) -> str:
        """
        Get Config Server URL (direct or via discovery).

        Returns:
            Config Server base URL

        Raises:
            ConfigServerError if URL cannot be determined
        """
        if self.config_server_url:
            logger.debug(f"Using direct Config Server URL: {self.config_server_url}")
            return self.config_server_url

        # Try Eureka discovery
        if self.service_discovery:
            return self._discover_config_server()

        raise ConfigServerError(
            "Config Server URL not provided and Eureka discovery not available. "
            "Set CONFIG_SERVER_URI or enable Eureka discovery."
        )

    def load_config(self) -> dict:
        """
        Load configuration from Config Server.

        Returns:
            Merged configuration dictionary

        Raises:
            ConfigServerError if loading fails and fail_fast=True
        """
        if not HAS_CONFIG_CLIENT:
            logger.error("Cannot load config: spring-config-client-python not installed")
            if self.fail_fast:
                raise ConfigServerError("spring-config-client-python not installed")
            return {}

        def _load():
            # Get config server URL
            server_url = self._get_config_server_url()

            # Create config client
            client = BaseConfigClient(
                server_url=server_url,
                app_name=self.app_name,
                profile=self.profile,
                username=self.username,
                password=self.password
            )

            # Fetch and load config into os.environ
            logger.info(f"Loading config for {self.app_name}/{self.profile} from {server_url}")
            config = client.fetch_and_load()

            logger.info(f"Loaded {len(config)} configuration properties")
            return config

        try:
            loaded_config = retry_with_backoff(
                func=_load,
                config=self.retry_config,
                operation_name="Config Server loading",
                fail_fast=self.fail_fast
            ) or {}

            # Store the loaded configuration
            self.config = loaded_config
            return loaded_config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            if self.fail_fast:
                raise ConfigServerError(f"Failed to load configuration: {e}") from e
            self.config = {}
            return {}

    @classmethod
    def from_env(
            cls,
            service_discovery: Optional[ServiceDiscovery] = None,
            fail_fast: bool = True
    ) -> "ConfigServerLoader":
        """
        Create ConfigServerLoader from environment variables.

        Environment variables:
        - SPRING_APPLICATION_NAME or APP_NAME: Application name
        - SPRING_PROFILES_ACTIVE: Active profile (default: default)
        - CONFIG_SERVER_URI: Direct Config Server URL (optional)
        - CONFIG_SERVER_SERVICE_ID: Config Server service ID in Eureka (default: CONFIG-SERVER)
        - CONFIG_SERVER_USERNAME: Basic auth username (optional)
        - CONFIG_SERVER_PASSWORD: Basic auth password (optional)

        Args:
            service_discovery: ServiceDiscovery instance for Eureka-based discovery
            fail_fast: If True, fail immediately on errors

        Returns:
            ConfigServerLoader instance
        """
        return cls(
            app_name=os.getenv("SPRING_APPLICATION_NAME") or os.getenv("APP_NAME", "application"),
            profile=os.getenv("SPRING_PROFILES_ACTIVE", "default"),
            config_server_url=os.getenv("CONFIG_SERVER_URI"),
            config_server_service_id=os.getenv("CONFIG_SERVER_SERVICE_ID", "CONFIG-SERVER"),
            service_discovery=service_discovery,
            username=os.getenv("CONFIG_SERVER_USERNAME"),
            password=os.getenv("CONFIG_SERVER_PASSWORD"),
            fail_fast=fail_fast
        )