"""
Actuator Beans Endpoint.
Shows information about application beans/components.
"""

import sys
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


class BeansEndpoint:
    """
    Beans endpoint for Spring Boot Actuator compatibility.

    Shows information about application components, similar to Spring's bean registry.
    In Python/FastAPI context, this includes:
    - Registered routes
    - Middleware components
    - Dependency injection components
    """

    def __init__(self, app: Optional['FastAPI'] = None):
        """
        Args:
            app: FastAPI application instance
        """
        self.app = app

    def get_beans(self) -> Dict[str, Any]:
        """
        Get all beans/components.

        Returns:
            Dictionary with application contexts and bean definitions
        """
        beans = {}

        if self.app:
            # Add FastAPI app itself
            beans["fastapi_app"] = {
                "type": "fastapi.applications.FastAPI",
                "scope": "singleton",
                "attributes": {
                    "title": self.app.title,
                    "version": self.app.version,
                    "openapi_url": self.app.openapi_url,
                }
            }

            # Add middleware
            middleware_beans = self._get_middleware_beans()
            beans.update(middleware_beans)

            # Add routes as beans
            route_beans = self._get_route_beans()
            beans.update(route_beans)

        # Add Python system components
        system_beans = self._get_system_beans()
        beans.update(system_beans)

        return {
            "contexts": {
                "application": {
                    "beans": beans,
                    "parentId": None
                }
            }
        }

    def _get_middleware_beans(self) -> Dict[str, Any]:
        """Get middleware components as beans"""
        middleware_beans = {}

        if not self.app or not hasattr(self.app, 'user_middleware'):
            return middleware_beans

        for idx, middleware in enumerate(self.app.user_middleware):
            middleware_cls = middleware.cls if hasattr(middleware, 'cls') else middleware
            bean_name = f"middleware_{idx}_{middleware_cls.__name__}"

            middleware_beans[bean_name] = {
                "type": f"{middleware_cls.__module__}.{middleware_cls.__name__}",
                "scope": "singleton",
                "attributes": {}
            }

        return middleware_beans

    def _get_route_beans(self) -> Dict[str, Any]:
        """Get routes as beans"""
        route_beans = {}

        if not self.app:
            return route_beans

        for route in self.app.routes:
            if hasattr(route, 'endpoint') and hasattr(route, 'path'):
                endpoint_name = route.endpoint.__name__ if hasattr(route.endpoint, '__name__') else str(route.endpoint)
                bean_name = f"route_{endpoint_name}_{route.path.replace('/', '_').replace('{', '').replace('}', '')}"

                route_beans[bean_name] = {
                    "type": "fastapi.routing.APIRoute",
                    "scope": "singleton",
                    "attributes": {
                        "path": route.path,
                        "methods": list(route.methods) if hasattr(route, 'methods') else [],
                        "name": route.name if hasattr(route, 'name') else None
                    }
                }

        return route_beans

    def _get_system_beans(self) -> Dict[str, Any]:
        """Get Python system components"""
        return {
            "python_interpreter": {
                "type": "system.python.interpreter",
                "scope": "singleton",
                "attributes": {
                    "version": sys.version.split()[0],
                    "executable": sys.executable,
                    "platform": sys.platform
                }
            }
        }


def create_default_beans_endpoint(app: Optional['FastAPI'] = None) -> BeansEndpoint:
    """
    Create beans endpoint with default configuration.

    Args:
        app: FastAPI application instance

    Returns:
        BeansEndpoint instance
    """
    return BeansEndpoint(app=app)
