"""
Actuator info endpoint.
Provides application metadata like Spring Boot Actuator's /actuator/info.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class InfoEndpoint:
    """
    Info endpoint that provides application metadata.

    Matches Spring Boot Actuator's info endpoint format:
    - app: Application info (name, version, description)
    - build: Build information
    - git: Git commit info (if available)
    - java: Runtime info (adapted for Python)
    """

    def __init__(
            self,
            app_name: Optional[str] = None,
            app_version: Optional[str] = None,
            app_description: Optional[str] = None
    ):
        self.app_name = app_name or os.getenv("SPRING_APPLICATION_NAME", "unknown")
        self.app_version = app_version or os.getenv("APP_VERSION", "unknown")
        self.app_description = app_description or os.getenv("APP_DESCRIPTION", "")
        self.custom_info: Dict[str, Any] = {}

    def add_info(self, key: str, value: Any) -> None:
        """Add custom info field"""
        self.custom_info[key] = value

    def get_info(self) -> Dict[str, Any]:
        """
        Get application info.

        Returns:
            Info response matching Spring Boot Actuator format
        """
        info = {
            "app": {
                "name": self.app_name,
                "version": self.app_version,
            }
        }

        if self.app_description:
            info["app"]["description"] = self.app_description

        # Python runtime info (equivalent to java info in Spring)
        info["python"] = {
            "version": sys.version,
            "vendor": sys.copyright.split("\n")[0] if sys.copyright else "Python Software Foundation",
            "runtime": {
                "name": "CPython",
                "version": sys.version.split()[0]
            },
            "jvm": {  # Keep "jvm" key for compatibility with Spring Admin
                "name": f"Python {sys.version.split()[0]}",
                "vendor": "Python Software Foundation",
                "version": sys.version.split()[0]
            }
        }

        # Build info from environment (if available)
        if any(os.getenv(k) for k in ["BUILD_NUMBER", "BUILD_TIME", "GIT_COMMIT"]):
            info["build"] = {}

            if build_number := os.getenv("BUILD_NUMBER"):
                info["build"]["number"] = build_number

            if build_time := os.getenv("BUILD_TIME"):
                info["build"]["time"] = build_time

            if git_commit := os.getenv("GIT_COMMIT"):
                info["build"]["commit"] = git_commit

        # Git info (if available)
        if git_commit := os.getenv("GIT_COMMIT"):
            info["git"] = {
                "commit": {
                    "id": git_commit,
                    "time": os.getenv("GIT_COMMIT_TIME", "")
                },
                "branch": os.getenv("GIT_BRANCH", "")
            }

        # Add custom info
        if self.custom_info:
            info.update(self.custom_info)

        return info


def create_default_info_endpoint(
        app_name: Optional[str] = None,
        app_version: Optional[str] = None,
        app_description: Optional[str] = None
) -> InfoEndpoint:
    """
    Create info endpoint with default configuration.

    Args:
        app_name: Application name (default from env)
        app_version: Application version (default from env)
        app_description: Application description (default from env)

    Returns:
        InfoEndpoint instance
    """
    return InfoEndpoint(
        app_name=app_name,
        app_version=app_version,
        app_description=app_description
    )