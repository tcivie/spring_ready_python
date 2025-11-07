"""
Actuator health endpoint.
Matches Spring Boot Actuator's /actuator/health format.
"""

import logging
from typing import Dict, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status values"""
    UP = "UP"
    DOWN = "DOWN"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    UNKNOWN = "UNKNOWN"


class HealthIndicator:
    """Base class for health indicators"""

    def __init__(self, name: str):
        self.name = name

    def health(self) -> Dict[str, Any]:
        """
        Check health and return status.

        Returns:
            Dictionary with 'status' and optional 'details'
        """
        raise NotImplementedError


class SimpleHealthIndicator(HealthIndicator):
    """Simple health indicator with a custom check function"""

    def __init__(self, name: str, check_func: Callable[[], bool]):
        super().__init__(name)
        self.check_func = check_func

    def health(self) -> Dict[str, Any]:
        try:
            is_healthy = self.check_func()
            return {
                "status": HealthStatus.UP.value if is_healthy else HealthStatus.DOWN.value
            }
        except Exception as e:
            logger.error(f"Health check '{self.name}' failed: {e}")
            return {
                "status": HealthStatus.DOWN.value,
                "details": {"error": str(e)}
            }


class HealthEndpoint:
    """
    Health endpoint that aggregates multiple health indicators.

    Matches Spring Boot Actuator's health endpoint behavior:
    - Overall status is DOWN if any indicator is DOWN
    - Shows details for each indicator
    """

    def __init__(self):
        self.indicators: Dict[str, HealthIndicator] = {}

    def add_indicator(self, indicator: HealthIndicator) -> None:
        """Add a health indicator"""
        self.indicators[indicator.name] = indicator

    def add_check(self, name: str, check_func: Callable[[], bool]) -> None:
        """
        Add a simple health check.

        Args:
            name: Health check name
            check_func: Function that returns True if healthy, False otherwise
        """
        self.add_indicator(SimpleHealthIndicator(name, check_func))

    def check(self) -> Dict[str, Any]:
        """
        Execute all health checks and aggregate results.

        Returns:
            Health response matching Spring Boot Actuator format
        """
        components = {}
        overall_status = HealthStatus.UP

        for name, indicator in self.indicators.items():
            try:
                component_health = indicator.health()
                components[name] = component_health

                # If any component is DOWN, the overall status is DOWN
                if component_health.get("status") == HealthStatus.DOWN.value:
                    overall_status = HealthStatus.DOWN

            except Exception as e:
                logger.error(f"Health indicator '{name}' threw exception: {e}")
                components[name] = {
                    "status": HealthStatus.DOWN.value,
                    "details": {"error": str(e)}
                }
                overall_status = HealthStatus.DOWN

        # If no indicators, default to UP
        if not components:
            overall_status = HealthStatus.UP

        return {
            "status": overall_status.value,
            "components": components
        }


def create_default_health_endpoint() -> HealthEndpoint:
    """
    Create a health endpoint with default indicators.

    Returns:
        HealthEndpoint with disk space and basic checks
    """
    health = HealthEndpoint()

    # Disk space check
    def check_disk_space() -> bool:
        import shutil
        try:
            stat = shutil.disk_usage("/")
            # Fail if less than 10MB free
            return stat.free > 10 * 1024 * 1024
        except Exception:
            return True  # Don't fail a health check on disk check error

    health.add_check("diskSpace", check_disk_space)

    # Ping check (always UP - just shows the app is responding)
    health.add_check("ping", lambda: True)

    return health