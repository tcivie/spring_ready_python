"""
Actuator Environment Endpoint.
Shows environment variables and configuration with sensitive value sanitization.
"""

import os
import sys
import re
from typing import Dict, Any, Optional, List


# Patterns for sensitive keys that should be sanitized
SENSITIVE_PATTERNS = [
    r'.*password.*',
    r'.*secret.*',
    r'.*key.*',
    r'.*token.*',
    r'.*credential.*',
    r'.*auth.*',
    r'.*api[_-]?key.*',
    r'.*private.*',
    r'.*salt.*',
    r'.*signature.*',
]


class EnvEndpoint:
    """
    Environment endpoint for Spring Boot Actuator compatibility.

    Shows environment variables and configuration properties.
    Automatically sanitizes sensitive values for security.
    """

    def __init__(self, sanitize: bool = True, custom_patterns: Optional[List[str]] = None):
        """
        Args:
            sanitize: Whether to sanitize sensitive values (default: True)
            custom_patterns: Additional regex patterns for sensitive keys
        """
        self.sanitize = sanitize
        self.sensitive_patterns = SENSITIVE_PATTERNS.copy()
        if custom_patterns:
            self.sensitive_patterns.extend(custom_patterns)

        # Compile patterns for efficiency
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.sensitive_patterns
        ]

    def _is_sensitive(self, key: str) -> bool:
        """
        Check if a key should be sanitized.

        Args:
            key: Environment variable key

        Returns:
            True if key matches sensitive patterns
        """
        if not self.sanitize:
            return False

        for pattern in self._compiled_patterns:
            if pattern.match(key):
                return True
        return False

    def _sanitize_value(self, value: str) -> str:
        """
        Sanitize a sensitive value.

        Args:
            value: Value to sanitize

        Returns:
            Sanitized value
        """
        return "******"

    def _get_property_dict(self, key: str, value: str) -> Dict[str, Any]:
        """
        Get property dictionary for a single environment variable.

        Args:
            key: Environment variable key
            value: Environment variable value

        Returns:
            Property dictionary with value and origin
        """
        is_sensitive = self._is_sensitive(key)
        display_value = self._sanitize_value(value) if is_sensitive else value

        return {
            "value": display_value,
            "origin": "System Environment"
        }

    def get_environment(self) -> Dict[str, Any]:
        """
        Get entire environment.

        Returns:
            Dictionary with active profiles and property sources
        """
        # Get active profile from environment
        active_profiles = []
        if profile := os.getenv("SPRING_PROFILES_ACTIVE"):
            active_profiles = [profile]

        # Build property sources
        properties = {}
        for key, value in os.environ.items():
            properties[key] = self._get_property_dict(key, value)

        return {
            "activeProfiles": active_profiles,
            "propertySources": [
                {
                    "name": "systemEnvironment",
                    "properties": properties
                }
            ]
        }

    def _get_synthetic_properties(self) -> Dict[str, str]:
        """
        Get synthetic properties that Spring Boot provides (like PID).

        Returns:
            Dictionary of synthetic property names and values
        """
        return {
            "PID": str(os.getpid()),
            "PYTHON_VERSION": sys.version.split()[0],
            "PYTHON_EXECUTABLE": sys.executable,
            "WORKING_DIRECTORY": os.getcwd(),
        }

    def get_property(self, property_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a single property by name.

        Args:
            property_name: Property name to lookup

        Returns:
            Property details or None if not found
        """
        # First check environment variables
        value = os.getenv(property_name)
        source_name = "systemEnvironment"

        # If not found, check synthetic properties
        if value is None:
            synthetic_props = self._get_synthetic_properties()
            value = synthetic_props.get(property_name)
            if value is not None:
                source_name = "systemProperties"

        # If still not found, return None
        if value is None:
            return None

        is_sensitive = self._is_sensitive(property_name)
        display_value = self._sanitize_value(value) if is_sensitive else value

        return {
            "property": {
                "source": source_name,
                "value": display_value
            },
            "activeProfiles": [os.getenv("SPRING_PROFILES_ACTIVE", "default")],
            "propertySources": [
                {
                    "name": source_name,
                    "property": {
                        "value": display_value,
                        "origin": "System Environment" if source_name == "systemEnvironment" else "System Properties"
                    }
                }
            ]
        }

    def add_sensitive_pattern(self, pattern: str) -> None:
        """
        Add a custom pattern for sensitive keys.

        Args:
            pattern: Regex pattern string
        """
        self.sensitive_patterns.append(pattern)
        self._compiled_patterns.append(re.compile(pattern, re.IGNORECASE))


def create_default_env_endpoint() -> EnvEndpoint:
    """
    Create env endpoint with default sanitization enabled.

    Returns:
        EnvEndpoint instance with sensitive value sanitization
    """
    return EnvEndpoint(sanitize=True)
