"""
Eureka REST API client.
Implements the Eureka REST endpoints for registration, heartbeat, and discovery.
"""

import requests
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin

from spring_ready.eureka.instance import InstanceInfo, InstanceStatus
from ..exceptions import EurekaRegistrationError, EurekaHeartbeatError, ServiceDiscoveryError

logger = logging.getLogger(__name__)


class EurekaClient:
    """
    Low-level Eureka REST API client.
    Handles HTTP communication with Eureka server.
    """

    def __init__(
            self,
            eureka_servers: List[str],
            timeout: int = 10
    ):
        """
        Args:
            eureka_servers: List of Eureka server URLs (e.g., ["http://eureka1:8761/eureka/"])
            timeout: Request timeout in seconds
        """
        self.eureka_servers = [url.rstrip('/') for url in eureka_servers]
        self.timeout = timeout
        self.current_server_idx = 0

        # Validate URLs
        self._validate_eureka_urls()

    def _validate_eureka_urls(self) -> None:
        """Validate Eureka server URLs and warn about common mistakes"""
        for url in self.eureka_servers:
            # Check if URL starts with http:// or https://
            if not url.startswith(('http://', 'https://')):
                logger.warning(
                    f"Eureka URL '{url}' does not start with http:// or https://. "
                    f"This may cause connection failures."
                )

            # Check if URL ends with /eureka (common mistake - missing trailing slash or /eureka)
            if not url.endswith('/eureka') and not url.endswith('/eureka/'):
                logger.warning(
                    f"Eureka URL '{url}' does not end with '/eureka/' or '/eureka'. "
                    f"This may cause connection failures. Expected format: http://host:port/eureka/"
                )

            # Warn if using localhost in URLs (common in containerized environments)
            if 'localhost' in url or '127.0.0.1' in url:
                logger.warning(
                    f"Eureka URL '{url}' uses localhost/127.0.0.1. "
                    f"This will not work in containerized environments (Docker, Kubernetes). "
                    f"Consider using service names or external IPs instead."
                )

    def _get_server_url(self) -> str:
        """Get current Eureka server URL with round-robin failover"""
        return self.eureka_servers[self.current_server_idx]

    def _next_server(self):
        """Move to next Eureka server in round-robin fashion"""
        self.current_server_idx = (self.current_server_idx + 1) % len(self.eureka_servers)

    def _request(
            self,
            method: str,
            path: str,
            **kwargs
    ) -> requests.Response:
        """
        Make HTTP request to Eureka with automatic failover.

        Args:
            method: HTTP method
            path: API path (e.g., "/apps/MY-APP")
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            Exception if all servers fail
        """
        last_error = None

        # Try all servers once
        for _ in range(len(self.eureka_servers)):
            server_url = self._get_server_url()
            url = urljoin(server_url + '/', path.lstrip('/'))

            try:
                logger.debug(f"Eureka {method} request to {url}")
                response = requests.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )

                # Eureka returns 204 for successful operations (not 200)
                if response.status_code in [200, 204]:
                    return response

                # Log non-success but don't fail immediately
                logger.warning(
                    f"Eureka request to {url} returned status {response.status_code}"
                )
                response.raise_for_status()

            except requests.RequestException as e:
                last_error = e
                logger.warning(f"Eureka request to {server_url} failed: {e}")
                self._next_server()
                continue

        # All servers failed
        raise last_error or Exception("All Eureka servers failed")

    def register(self, instance: InstanceInfo) -> None:
        """
        Register instance with Eureka.

        POST /eureka/apps/{app-name}

        Args:
            instance: Instance information

        Raises:
            EurekaRegistrationError if registration fails
        """
        try:
            path = f"/apps/{instance.app}"
            response = self._request(
                method="POST",
                path=path,
                json=instance.to_eureka_dict(),
                headers={"Content-Type": "application/json"}
            )

            logger.info(
                f"Registered instance {instance.instance_id} with Eureka at "
                f"{self._get_server_url()}"
            )

        except Exception as e:
            raise EurekaRegistrationError(
                f"Failed to register with Eureka: {e}"
            ) from e

    def send_heartbeat(self, app_name: str, instance_id: str) -> None:
        """
        Send heartbeat to Eureka.

        PUT /eureka/apps/{app-name}/{instance-id}

        Args:
            app_name: Application name (uppercase)
            instance_id: Instance ID

        Raises:
            EurekaHeartbeatError if heartbeat fails
        """
        try:
            path = f"/apps/{app_name}/{instance_id}"
            response = self._request(
                method="PUT",
                path=path,
                params={"status": "UP"}
            )

            logger.debug(f"Heartbeat sent for {instance_id}")

        except Exception as e:
            raise EurekaHeartbeatError(
                f"Failed to send heartbeat: {e}"
            ) from e

    def deregister(self, app_name: str, instance_id: str) -> None:
        """
        Deregister instance from Eureka.

        DELETE /eureka/apps/{app-name}/{instance-id}

        Args:
            app_name: Application name (uppercase)
            instance_id: Instance ID
        """
        try:
            path = f"/apps/{app_name}/{instance_id}"
            response = self._request(
                method="DELETE",
                path=path
            )

            logger.info(f"Deregistered instance {instance_id} from Eureka")

        except Exception as e:
            logger.error(f"Failed to deregister from Eureka: {e}")

    def get_applications(self) -> Dict[str, Any]:
        """
        Get all registered applications from Eureka.

        GET /eureka/apps

        Returns:
            Dictionary containing all applications and their instances

        Raises:
            ServiceDiscoveryError if request fails
        """
        try:
            response = self._request(
                method="GET",
                path="/apps",
                headers={"Accept": "application/json"}
            )

            return response.json()

        except Exception as e:
            raise ServiceDiscoveryError(
                f"Failed to fetch applications from Eureka: {e}"
            ) from e

    def get_application(self, app_name: str) -> Dict[str, Any]:
        """
        Get specific application instances from Eureka.

        GET /eureka/apps/{app-name}

        Args:
            app_name: Application name (uppercase)

        Returns:
            Dictionary containing application instances

        Raises:
            ServiceDiscoveryError if request fails
        """
        try:
            response = self._request(
                method="GET",
                path=f"/apps/{app_name}",
                headers={"Accept": "application/json"}
            )

            return response.json()

        except Exception as e:
            raise ServiceDiscoveryError(
                f"Failed to fetch application {app_name} from Eureka: {e}"
            ) from e

    def update_status(
            self,
            app_name: str,
            instance_id: str,
            status: InstanceStatus
    ) -> None:
        """
        Update instance status in Eureka.

        PUT /eureka/apps/{app-name}/{instance-id}/status

        Args:
            app_name: Application name (uppercase)
            instance_id: Instance ID
            status: New status
        """
        try:
            path = f"/apps/{app_name}/{instance_id}/status"
            response = self._request(
                method="PUT",
                path=path,
                params={"value": status.value}
            )

            logger.info(f"Updated status for {instance_id} to {status.value}")

        except Exception as e:
            logger.error(f"Failed to update status: {e}")