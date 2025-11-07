"""
Exponential backoff retry logic.
Matches Spring Cloud Config's retry behavior.
"""

import time
import logging
from typing import Callable, TypeVar, Optional

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for exponential backoff retry"""

    def __init__(
            self,
            max_attempts: int = 6,
            initial_interval: float = 1.0,
            max_interval: float = 2.0,
            multiplier: float = 1.1
    ):
        """
        Args:
            max_attempts: Maximum number of retry attempts
            initial_interval: Initial retry interval in seconds
            max_interval: Maximum retry interval in seconds
            multiplier: Multiplier for exponential backoff
        """
        self.max_attempts = max_attempts
        self.initial_interval = initial_interval
        self.max_interval = max_interval
        self.multiplier = multiplier


def retry_with_backoff(
        func: Callable[[], T],
        config: RetryConfig,
        operation_name: str,
        fail_fast: bool = True
) -> Optional[T]:
    """
    Execute function with exponential backoff retry.

    Args:
        func: Function to execute
        config: Retry configuration
        operation_name: Name of operation for logging
        fail_fast: If True, raise exception after max attempts. If False, return None.

    Returns:
        Result of func() if successful, None if fail_fast=False and all retries exhausted

    Raises:
        Last exception if fail_fast=True and all retries exhausted
    """
    last_exception = None
    interval = config.initial_interval

    for attempt in range(1, config.max_attempts + 1):
        try:
            logger.debug(f"{operation_name}: Attempt {attempt}/{config.max_attempts}")
            result = func()

            if attempt > 1:
                logger.info(f"{operation_name}: Succeeded on attempt {attempt}")

            return result

        except Exception as e:
            last_exception = e

            if attempt == config.max_attempts:
                logger.error(
                    f"{operation_name}: Failed after {config.max_attempts} attempts. "
                    f"Last error: {e}"
                )
                if fail_fast:
                    raise
                return None

            logger.warning(
                f"{operation_name}: Attempt {attempt} failed: {e}. "
                f"Retrying in {interval:.2f}s..."
            )

            time.sleep(interval)

            # Exponential backoff with max limit
            interval = min(interval * config.multiplier, config.max_interval)

    # Should not reach here, but just in case
    if fail_fast and last_exception:
        raise last_exception
    return None