"""
Actuator ConfigProps Endpoint.
Shows configuration properties grouped by prefix.
"""

import os
from typing import Dict, Any


class ConfigPropsEndpoint:
    """
    ConfigProps endpoint for Spring Boot Actuator compatibility.

    Shows configuration properties similar to Spring Boot's @ConfigurationProperties.
    Groups environment variables and settings by common prefixes.
    """

    def get_config_props(self) -> Dict[str, Any]:
        """
        Get all configuration properties grouped by prefix.

        Returns:
            Dictionary with configuration property beans
        """
        # Group environment variables by common prefixes
        grouped_props = self._group_by_prefix(dict(os.environ))

        beans = {}
        for prefix, props in grouped_props.items():
            bean_name = f"{prefix}_properties"
            beans[bean_name] = {
                "prefix": prefix,
                "properties": props
            }

        return {
            "contexts": {
                "application": {
                    "beans": beans
                }
            }
        }

    def get_config_props_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """
        Get configuration properties filtered by prefix.

        Args:
            prefix: Prefix to filter by

        Returns:
            Dictionary with matching configuration properties
        """
        matching_props = {}

        for key, value in os.environ.items():
            if key.startswith(prefix.upper()) or key.lower().startswith(prefix.lower()):
                matching_props[key] = value

        if not matching_props:
            return {}

        bean_name = f"{prefix}_properties"
        return {
            "contexts": {
                "application": {
                    "beans": {
                        bean_name: {
                            "prefix": prefix,
                            "properties": matching_props
                        }
                    }
                }
            }
        }

    def _group_by_prefix(self, env_vars: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """
        Group environment variables by common prefixes.

        Args:
            env_vars: Environment variables dictionary

        Returns:
            Dictionary grouped by prefix
        """
        grouped = {}

        for key, value in env_vars.items():
            # Extract prefix (first part before _)
            parts = key.split('_', 1)
            prefix = parts[0] if parts else key

            if prefix not in grouped:
                grouped[prefix] = {}

            grouped[prefix][key] = value

        return grouped


def create_default_configprops_endpoint() -> ConfigPropsEndpoint:
    """
    Create configprops endpoint with default configuration.

    Returns:
        ConfigPropsEndpoint instance
    """
    return ConfigPropsEndpoint()
