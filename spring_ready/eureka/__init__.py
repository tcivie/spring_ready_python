"""Eureka service registration and discovery"""

from .client import EurekaClient
from .instance import InstanceInfo, InstanceStatus
from .registry import EurekaRegistry
from .discovery import ServiceDiscovery, ServiceInstance

__all__ = [
    "EurekaClient",
    "InstanceInfo",
    "InstanceStatus",
    "EurekaRegistry",
    "ServiceDiscovery",
    "ServiceInstance",
]