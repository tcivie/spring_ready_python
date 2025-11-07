"""
Actuator Logfile Endpoint.
Provides access to application log files.
"""

import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LogfileEndpoint:
    """
    Logfile endpoint for Spring Boot Actuator compatibility.

    Provides access to application log files with support for:
    - Full log file retrieval
    - Partial retrieval with Range header support
    """

    def __init__(self, log_file_path: Optional[str] = None):
        """
        Args:
            log_file_path: Path to the log file (default: None, which means no log file)
        """
        self.log_file_path = log_file_path

        # Verify log file exists if path provided
        if self.log_file_path and not os.path.exists(self.log_file_path):
            logger.warning(f"Log file not found: {self.log_file_path}")

    def get_logfile(self, range_header: Optional[str] = None) -> tuple[Optional[bytes], Optional[str], int]:
        """
        Get log file contents.

        Args:
            range_header: HTTP Range header value (e.g., "bytes=0-1023")

        Returns:
            Tuple of (content, content_range_header, status_code)
            - content: Log file bytes or None if not available
            - content_range_header: Content-Range header value or None
            - status_code: HTTP status code (200, 206, or 404)
        """
        # If no log file configured
        if not self.log_file_path:
            logger.warning("No log file configured for logfile endpoint")
            return None, None, 404

        # If log file doesn't exist
        if not os.path.exists(self.log_file_path):
            logger.warning(f"Log file not found: {self.log_file_path}")
            return None, None, 404

        try:
            file_size = os.path.getsize(self.log_file_path)

            # Handle range request
            if range_header:
                # Parse range header (e.g., "bytes=0-1023")
                if range_header.startswith("bytes="):
                    range_spec = range_header[6:]
                    start, end = self._parse_range(range_spec, file_size)

                    if start is None or end is None:
                        # Invalid range
                        return None, None, 416  # Range Not Satisfiable

                    # Read the specified range
                    with open(self.log_file_path, 'rb') as f:
                        f.seek(start)
                        content = f.read(end - start + 1)

                    # Build Content-Range header
                    content_range = f"bytes {start}-{end}/{file_size}"
                    return content, content_range, 206  # Partial Content

            # Read entire file
            with open(self.log_file_path, 'rb') as f:
                content = f.read()

            return content, None, 200

        except Exception as e:
            logger.error(f"Error reading log file: {e}", exc_info=True)
            return None, None, 500

    def _parse_range(self, range_spec: str, file_size: int) -> tuple[Optional[int], Optional[int]]:
        """
        Parse HTTP Range specification.

        Args:
            range_spec: Range specification (e.g., "0-1023" or "-1024" or "1024-")
            file_size: Total file size

        Returns:
            Tuple of (start, end) byte positions, or (None, None) if invalid
        """
        try:
            if '-' not in range_spec:
                return None, None

            parts = range_spec.split('-', 1)

            # Handle "-1024" (last 1024 bytes)
            if not parts[0]:
                suffix_length = int(parts[1])
                start = max(0, file_size - suffix_length)
                end = file_size - 1
                return start, end

            # Handle "1024-" (from byte 1024 to end)
            if not parts[1]:
                start = int(parts[0])
                end = file_size - 1
                return start, end

            # Handle "0-1023" (bytes 0 to 1023)
            start = int(parts[0])
            end = int(parts[1])

            # Validate range
            if start < 0 or end >= file_size or start > end:
                return None, None

            return start, end

        except (ValueError, IndexError):
            return None, None

    def is_available(self) -> bool:
        """Check if log file is available"""
        return (
            self.log_file_path is not None
            and os.path.exists(self.log_file_path)
        )


def create_default_logfile_endpoint(log_file_path: Optional[str] = None) -> LogfileEndpoint:
    """
    Create logfile endpoint with default configuration.

    Automatically detects log file from Python logging handlers if not specified.
    Priority: explicit parameter > LOG_FILE_PATH env var > auto-detected from logging

    Args:
        log_file_path: Path to log file (default: auto-detect or from env LOG_FILE_PATH)

    Returns:
        LogfileEndpoint instance
    """
    # Priority 1: Explicit parameter
    if log_file_path is not None:
        return LogfileEndpoint(log_file_path=log_file_path)

    # Priority 2: Environment variable
    log_file_path = os.getenv("LOG_FILE_PATH")
    if log_file_path is not None:
        return LogfileEndpoint(log_file_path=log_file_path)

    # Priority 3: Auto-detect from Python logging handlers
    log_file_path = _auto_detect_log_file()

    return LogfileEndpoint(log_file_path=log_file_path)


def _auto_detect_log_file() -> Optional[str]:
    """
    Auto-detect log file path from Python logging configuration.

    Scans all logging handlers for FileHandler, RotatingFileHandler,
    TimedRotatingFileHandler and extracts the file path.

    Returns:
        Detected log file path or None if no file handler found
    """
    try:
        # Check root logger first
        for handler in logging.root.handlers:
            if isinstance(handler, logging.FileHandler):
                log_path = handler.baseFilename
                logger.info(f"Auto-detected log file: {log_path}")
                return log_path

        # Check all other loggers
        for logger_name in logging.Logger.manager.loggerDict:
            log_instance = logging.getLogger(logger_name)
            if hasattr(log_instance, 'handlers'):
                for handler in log_instance.handlers:
                    if isinstance(handler, logging.FileHandler):
                        log_path = handler.baseFilename
                        logger.info(f"Auto-detected log file from logger '{logger_name}': {log_path}")
                        return log_path

        logger.debug("No log file found in logging configuration")
        return None
    except Exception as e:
        logger.warning(f"Failed to auto-detect log file: {e}")
        return None
