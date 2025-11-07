"""
Actuator Discovery Endpoint.
Returns HAL JSON format with links to all available actuator endpoints.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ActuatorLink:
    """Represents a single actuator endpoint link"""
    href: str
    templated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "href": self.href,
            "templated": self.templated
        }


class ActuatorDiscoveryEndpoint:
    """
    Discovery endpoint that returns HAL JSON with links to all actuator endpoints.

    Implements Spring Boot's /actuator discovery endpoint format.
    """

    def __init__(self, base_url: str):
        """
        Args:
            base_url: Base URL for the application (e.g., "http://localhost:8080")
        """
        self.base_url = base_url.rstrip('/')
        self.endpoints: Dict[str, ActuatorLink] = {}

        # Always include self link
        self.endpoints["self"] = ActuatorLink(
            href=f"{self.base_url}/actuator",
            templated=False
        )

    def register_endpoint(self, name: str, path: str, templated: bool = False) -> None:
        """
        Register an actuator endpoint.

        Args:
            name: Endpoint name (e.g., "health", "info")
            path: Endpoint path relative to /actuator (e.g., "/health")
            templated: Whether the endpoint uses URI templates
        """
        path = path.lstrip('/')
        self.endpoints[name] = ActuatorLink(
            href=f"{self.base_url}/actuator/{path}",
            templated=templated
        )

    def register_templated_endpoint(self, name: str, path: str) -> None:
        """
        Register a templated actuator endpoint (uses URI templates).

        Args:
            name: Endpoint name (e.g., "health-path", "metrics-requiredMetricName")
            path: Endpoint path with template variables (e.g., "/health/{*path}")
        """
        self.register_endpoint(name, path, templated=True)

    def get_links(self) -> Dict[str, Any]:
        """
        Get all endpoint links in HAL JSON format.

        Returns:
            Dictionary with "_links" structure
        """
        return {
            "_links": {
                name: link.to_dict()
                for name, link in self.endpoints.items()
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Get discovery endpoint response.

        Returns:
            HAL JSON response with _links
        """
        return self.get_links()


def create_default_discovery_endpoint(base_url: str) -> ActuatorDiscoveryEndpoint:
    """
    Create discovery endpoint with common actuator endpoints registered.

    Args:
        base_url: Base URL for the application

    Returns:
        ActuatorDiscoveryEndpoint instance with standard endpoints
    """
    discovery = ActuatorDiscoveryEndpoint(base_url)

    # Register standard endpoints
    discovery.register_endpoint("health", "health")
    discovery.register_templated_endpoint("health-path", "health/{*path}")
    discovery.register_endpoint("info", "info")
    discovery.register_endpoint("prometheus", "prometheus")
    discovery.register_endpoint("metrics", "metrics")
    discovery.register_templated_endpoint("metrics-requiredMetricName", "metrics/{requiredMetricName}")
    discovery.register_endpoint("env", "env")
    discovery.register_templated_endpoint("env-toMatch", "env/{toMatch}")
    discovery.register_endpoint("loggers", "loggers")
    discovery.register_templated_endpoint("loggers-name", "loggers/{name}")
    discovery.register_endpoint("mappings", "mappings")
    discovery.register_endpoint("threaddump", "threaddump")
    discovery.register_endpoint("httptrace", "httptrace")
    discovery.register_endpoint("httpexchanges", "httpexchanges")
    discovery.register_endpoint("logfile", "logfile")
    discovery.register_endpoint("refresh", "refresh")
    discovery.register_endpoint("beans", "beans")
    discovery.register_endpoint("configprops", "configprops")
    discovery.register_templated_endpoint("configprops-prefix", "configprops/{prefix}")
    discovery.register_endpoint("scheduledtasks", "scheduledtasks")
    discovery.register_endpoint("heapdump", "heapdump")
    discovery.register_endpoint("caches", "caches")
    discovery.register_templated_endpoint("caches-cache", "caches/{cache}")
    discovery.register_endpoint("auditevents", "auditevents")

    return discovery
