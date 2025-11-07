"""
Service discovery helper.
Find and resolve other services registered in Eureka.
"""

import random
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from .client import EurekaClient
from ..exceptions import ServiceDiscoveryError

logger = logging.getLogger(__name__)


class ServiceInstance:
    """Represents a discovered service instance"""

    def __init__(self, instance_data: Dict[str, Any]):
        """
        Args:
            instance_data: Raw instance data from Eureka
        """
        self.instance_id = instance_data.get("instanceId", "")
        self.host_name = instance_data.get("hostName", "")
        self.ip_addr = instance_data.get("ipAddr", "")
        self.app = instance_data.get("app", "")
        self.status = instance_data.get("status", "UNKNOWN")

        # Extract port info
        port_info = instance_data.get("port", {})
        self.port = port_info.get("$", 80) if isinstance(port_info, dict) else port_info

        secure_port_info = instance_data.get("securePort", {})
        self.secure_port = secure_port_info.get("$", 443) if isinstance(secure_port_info, dict) else secure_port_info

        # URLs
        self.home_page_url = instance_data.get("homePageUrl", "")
        self.status_page_url = instance_data.get("statusPageUrl", "")
        self.health_check_url = instance_data.get("healthCheckUrl", "")

        # Metadata
        self.metadata = instance_data.get("metadata", {})

    @property
    def base_url(self) -> str:
        """Get base URL for this instance"""
        return f"http://{self.ip_addr}:{self.port}"

    @property
    def is_up(self) -> bool:
        """Check if instance is UP"""
        return self.status == "UP"

    def __repr__(self) -> str:
        return f"ServiceInstance(app={self.app}, instance_id={self.instance_id}, url={self.base_url}, status={self.status})"


class ServiceDiscovery:
    """
    Service discovery client for finding other services in Eureka.

    Usage:
        discovery = ServiceDiscovery(eureka_client)

        # Get all instances of a service
        instances = discovery.get_instances("config-server")

        # Get a single instance (with load balancing)
        instance = discovery.get_instance("config-server")

        # Get service URL
        url = discovery.get_service_url("config-server")
    """

    def __init__(self, eureka_client: EurekaClient):
        """
        Args:
            eureka_client: Eureka client for API communication
        """
        self.client = eureka_client

    def get_instances(self, service_name: str, only_up: bool = True) -> List[ServiceInstance]:
        """
        Get all instances of a service.

        Args:
            service_name: Service name (case-insensitive)
            only_up: If True, only return instances with status=UP

        Returns:
            List of ServiceInstance objects

        Raises:
            ServiceDiscoveryError if service not found
        """
        try:
            # Eureka stores app names in uppercase
            app_name = service_name.upper()

            response = self.client.get_application(app_name)

            # Parse response
            application = response.get("application", {})
            instances_data = application.get("instance", [])

            # Ensure it's a list (Eureka returns single object if only one instance)
            if isinstance(instances_data, dict):
                instances_data = [instances_data]

            # Convert to ServiceInstance objects
            instances = [ServiceInstance(data) for data in instances_data]

            # Filter by status if requested
            if only_up:
                instances = [inst for inst in instances if inst.is_up]

            if not instances:
                raise ServiceDiscoveryError(
                    f"No {'UP ' if only_up else ''}instances found for service: {service_name}"
                )

            logger.debug(f"Found {len(instances)} instances for {service_name}")
            return instances

        except ServiceDiscoveryError:
            raise
        except Exception as e:
            raise ServiceDiscoveryError(
                f"Failed to discover service {service_name}: {e}"
            ) from e

    def get_instance(
            self,
            service_name: str,
            load_balance: bool = True
    ) -> ServiceInstance:
        """
        Get a single instance of a service.

        Args:
            service_name: Service name
            load_balance: If True, randomly select from available instances

        Returns:
            ServiceInstance object

        Raises:
            ServiceDiscoveryError if service not found
        """
        instances = self.get_instances(service_name, only_up=True)

        if not instances:
            raise ServiceDiscoveryError(f"No instances available for {service_name}")

        # Random selection for simple client-side load balancing
        if load_balance and len(instances) > 1:
            return random.choice(instances)

        return instances[0]

    def get_service_url(self, service_name: str) -> str:
        """
        Get base URL for a service.

        Args:
            service_name: Service name

        Returns:
            Base URL (e.g., "http://10.10.0.1:8888")

        Raises:
            ServiceDiscoveryError if service not found
        """
        instance = self.get_instance(service_name)
        return instance.base_url

    def list_services(self) -> List[str]:
        """
        List all registered service names in Eureka.

        Returns:
            List of service names (uppercase)
        """
        try:
            response = self.client.get_applications()
            applications = response.get("applications", {}).get("application", [])

            # Ensure it's a list
            if isinstance(applications, dict):
                applications = [applications]

            return [app.get("name", "") for app in applications]

        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return []