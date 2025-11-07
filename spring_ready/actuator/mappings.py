"""
Actuator Mappings Endpoint.
Shows all registered request mappings (routes) in the application.
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.routing import APIRoute


class MappingsEndpoint:
    """
    Mappings endpoint for Spring Boot Actuator compatibility.

    Shows all registered FastAPI routes with their HTTP methods and handlers.
    """

    def __init__(self, app: FastAPI):
        """
        Args:
            app: FastAPI application instance
        """
        self.app = app

    def get_mappings(self) -> Dict[str, Any]:
        """
        Get all request mappings.

        Returns:
            Dictionary with contexts and dispatcher servlet mappings
        """
        mappings = []

        # Iterate through all routes
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                # Get handler info
                handler_name = route.endpoint.__name__ if hasattr(route, 'endpoint') else "unknown"
                handler_module = route.endpoint.__module__ if hasattr(route, 'endpoint') else "unknown"

                # Get methods
                methods = list(route.methods) if hasattr(route, 'methods') else []

                # Build mapping entry
                mapping = {
                    "handler": f"{handler_module}.{handler_name}",
                    "predicate": f"{{{', '.join(methods)}}} {route.path}",
                    "details": {
                        "requestMappingConditions": {
                            "methods": methods,
                            "patterns": [route.path]
                        }
                    }
                }

                mappings.append(mapping)

        return {
            "contexts": {
                "application": {
                    "mappings": {
                        "dispatcherServlet": {
                            "details": {
                                "requestMappingConditions": {
                                    "patterns": []
                                }
                            },
                            "dispatcherHandlers": {
                                "webHandler": mappings
                            }
                        }
                    }
                }
            }
        }


def create_default_mappings_endpoint(app: FastAPI) -> MappingsEndpoint:
    """
    Create mappings endpoint for a FastAPI application.

    Args:
        app: FastAPI application instance

    Returns:
        MappingsEndpoint instance
    """
    return MappingsEndpoint(app)
