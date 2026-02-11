"""
Spring-Ready Python
A lightweight library to make Python apps Spring Boot ecosystem compatible.

Provides:
- Eureka service registration
- Config Server integration with discovery
- Actuator endpoints (health, info, prometheus)
- FastAPI integration

Usage:
    from spring_ready import SpringReadyApp

    app = SpringReadyApp()
"""

from .core import SpringReadyApp
from .exceptions import (
    SpringReadyException,
    EurekaRegistrationError,
    EurekaHeartbeatError,
    EurekaInstanceNotFoundError,
    ConfigServerError,
)

__version__ = "1.1.2"
__all__ = [
    "SpringReadyApp",
    "SpringReadyException",
    "EurekaRegistrationError",
    "EurekaHeartbeatError",
    "EurekaInstanceNotFoundError",
    "ConfigServerError",
]