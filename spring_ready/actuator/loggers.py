"""
Actuator Loggers Endpoint.
Shows and manages logger configurations and levels.
"""

import logging
from typing import Dict, Any, Optional, List


# Valid log levels
VALID_LEVELS = ["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL", "OFF"]

# Map Spring Boot levels to Python levels
LEVEL_MAPPING = {
    "TRACE": logging.DEBUG,  # Python doesn't have TRACE, use DEBUG
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "OFF": logging.CRITICAL + 10,  # Effectively disable logging
}

# Reverse mapping for display
PYTHON_TO_SPRING = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARN",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRITICAL",
}


class LoggersEndpoint:
    """
    Loggers endpoint for Spring Boot Actuator compatibility.

    Provides:
    - List all loggers with their levels
    - Get individual logger configuration
    - Set/update logger levels
    - Clear logger levels (reset to inherited)
    """

    def __init__(self):
        """Initialize loggers endpoint"""
        pass

    def _get_logger_level_name(self, level: Optional[int]) -> Optional[str]:
        """
        Convert Python log level to Spring Boot level name.

        Args:
            level: Python log level integer

        Returns:
            Spring Boot level name or None
        """
        if level is None:
            return None
        return PYTHON_TO_SPRING.get(level, "DEBUG")

    def _get_logger_info(self, logger: logging.Logger) -> Dict[str, Any]:
        """
        Get logger information.

        Args:
            logger: Logger instance

        Returns:
            Dictionary with configuredLevel and effectiveLevel
        """
        # Get configured level (may be None if inherited)
        configured_level = logger.level if logger.level != logging.NOTSET else None
        configured_level_name = self._get_logger_level_name(configured_level)

        # Get effective level (always has a value due to inheritance)
        effective_level = logger.getEffectiveLevel()
        effective_level_name = self._get_logger_level_name(effective_level)

        return {
            "configuredLevel": configured_level_name,
            "effectiveLevel": effective_level_name
        }

    def get_all_loggers(self) -> Dict[str, Any]:
        """
        Get all loggers.

        Returns:
            Dictionary with levels list and loggers dict
        """
        loggers_dict = {}

        # Get root logger
        root_logger = logging.getLogger()
        loggers_dict["ROOT"] = self._get_logger_info(root_logger)

        # Get all other loggers
        # Access the internal logger dictionary
        logger_dict = logging.Logger.manager.loggerDict
        for name, logger_item in sorted(logger_dict.items()):
            # Skip PlaceHolder objects, only include actual Logger instances
            if isinstance(logger_item, logging.Logger):
                loggers_dict[name] = self._get_logger_info(logger_item)

        return {
            "levels": VALID_LEVELS,
            "loggers": loggers_dict,
            "groups": {}
        }

    def get_logger(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a single logger by name.

        Args:
            name: Logger name (use "ROOT" for root logger)

        Returns:
            Logger info or None if not found
        """
        if name == "ROOT":
            logger = logging.getLogger()
        else:
            # Check if logger exists
            if name not in logging.Logger.manager.loggerDict:
                return None
            logger = logging.getLogger(name)

        return self._get_logger_info(logger)

    def set_logger_level(self, name: str, level: Optional[str]) -> bool:
        """
        Set logger level.

        Args:
            name: Logger name (use "ROOT" for root logger)
            level: Level name (DEBUG, INFO, WARN, ERROR, etc.) or None to clear

        Returns:
            True if successful, False if logger not found or invalid level
        """
        # Validate level
        if level is not None and level not in LEVEL_MAPPING:
            return False

        # Get logger
        if name == "ROOT":
            logger = logging.getLogger()
        else:
            logger = logging.getLogger(name)

        # Set level
        if level is None:
            # Clear level (set to NOTSET to inherit from parent)
            logger.setLevel(logging.NOTSET)
        else:
            python_level = LEVEL_MAPPING[level]
            logger.setLevel(python_level)

        return True

    def clear_logger_level(self, name: str) -> bool:
        """
        Clear logger level (reset to inherited).

        Args:
            name: Logger name

        Returns:
            True if successful
        """
        return self.set_logger_level(name, None)


def create_default_loggers_endpoint() -> LoggersEndpoint:
    """
    Create loggers endpoint.

    Returns:
        LoggersEndpoint instance
    """
    return LoggersEndpoint()
