"""
Eureka service registry manager.
Handles registration, heartbeat thread, and graceful deregistration.
"""

import time
import threading
import logging
import atexit
from typing import Optional, List

from .client import EurekaClient
from .instance import InstanceInfo, InstanceStatus
from ..exceptions import EurekaRegistrationError, EurekaHeartbeatError
from ..retry import retry_with_backoff, RetryConfig

logger = logging.getLogger(__name__)


class EurekaRegistry:
    """
    High-level Eureka service registry manager.

    Responsibilities:
    - Register with Eureka on startup
    - Send periodic heartbeats
    - Deregister on shutdown
    """

    def __init__(
            self,
            eureka_servers: List[str],
            instance_info: InstanceInfo,
            retry_config: Optional[RetryConfig] = None,
            fail_fast: bool = True
    ):
        """
        Args:
            eureka_servers: List of Eureka server URLs
            instance_info: Instance metadata
            retry_config: Retry configuration for registration
            fail_fast: If True, fail immediately if registration fails after retries
        """
        self.client = EurekaClient(eureka_servers)
        self.instance = instance_info
        self.retry_config = retry_config or RetryConfig()
        self.fail_fast = fail_fast

        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_heartbeat = threading.Event()
        self._registered = False

        # Register shutdown hook
        atexit.register(self.shutdown)

    def start(self) -> None:
        """
        Register with Eureka and start heartbeat thread.

        Raises:
            EurekaRegistrationError if registration fails and fail_fast=True
        """

        # Register with retry
        def _register():
            self.client.register(self.instance)
            self._registered = True

        logger.info(f"Registering {self.instance.instance_id} with Eureka...")

        retry_with_backoff(
            func=_register,
            config=self.retry_config,
            operation_name="Eureka registration",
            fail_fast=self.fail_fast
        )

        if not self._registered:
            logger.warning("Failed to register with Eureka, but continuing anyway")
            return

        # Start heartbeat thread
        self._start_heartbeat_thread()

        logger.info(f"Eureka registration completed for {self.instance.instance_id}")

    def _start_heartbeat_thread(self) -> None:
        """Start background thread for sending heartbeats"""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            logger.warning("Heartbeat thread already running")
            return

        self._stop_heartbeat.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"eureka-heartbeat-{self.instance.instance_id}",
            daemon=True
        )
        self._heartbeat_thread.start()

        logger.info("Heartbeat thread started")

    def _heartbeat_loop(self) -> None:
        """
        Background thread that sends periodic heartbeats to Eureka.

        Matches Spring's behavior:
        - Sends heartbeat every renewal_interval_in_secs (default: 30s)
        - Logs warnings on failure but doesn't crash
        - Uses exponential backoff on consecutive failures
        """
        interval = self.instance.lease_info.renewal_interval_in_secs
        consecutive_failures = 0

        while not self._stop_heartbeat.wait(timeout=interval):
            try:
                self.client.send_heartbeat(
                    app_name=self.instance.app,
                    instance_id=self.instance.instance_id
                )

                # Reset failure count on success
                if consecutive_failures > 0:
                    logger.info("Heartbeat recovered after failures")
                    consecutive_failures = 0

            except EurekaHeartbeatError as e:
                consecutive_failures += 1
                logger.warning(
                    f"Heartbeat failed (attempt {consecutive_failures}): {e}"
                )

                # Exponential backoff on failures, but cap at 2x the normal interval
                backoff_multiplier = min(1.5 ** (consecutive_failures - 1), 2.0)
                interval = self.instance.lease_info.renewal_interval_in_secs * backoff_multiplier

                # Don't crash the app on heartbeat failure - Eureka will eventually evict
                # the instance if heartbeats stop, but the app can keep serving requests

            except Exception as e:
                logger.error(f"Unexpected error in heartbeat thread: {e}", exc_info=True)

        logger.info("Heartbeat thread stopped")

    def update_status(self, status: InstanceStatus) -> None:
        """
        Update instance status in Eureka.

        Args:
            status: New status (UP, DOWN, OUT_OF_SERVICE, etc.)
        """
        if not self._registered:
            logger.warning("Cannot update status: not registered with Eureka")
            return

        try:
            self.client.update_status(
                app_name=self.instance.app,
                instance_id=self.instance.instance_id,
                status=status
            )
            self.instance.status = status
        except Exception as e:
            logger.error(f"Failed to update status: {e}")

    def shutdown(self) -> None:
        """
        Gracefully shutdown: stop heartbeat and deregister from Eureka.
        Called automatically on process exit via atexit.
        """
        if not self._registered:
            return

        logger.info(f"Shutting down Eureka registry for {self.instance.instance_id}")

        # Stop heartbeat thread
        self._stop_heartbeat.set()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)

        # Deregister from Eureka
        try:
            self.client.deregister(
                app_name=self.instance.app,
                instance_id=self.instance.instance_id
            )
            self._registered = False
        except Exception as e:
            logger.error(f"Failed to deregister from Eureka: {e}")

        logger.info("Eureka registry shutdown complete")