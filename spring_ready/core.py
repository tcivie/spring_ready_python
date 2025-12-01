"""
Main SpringReadyApp class.
One-stop solution for making Python apps Spring Boot ecosystem compatible.
"""

import os
import logging
from typing import Optional, List
from fastapi import FastAPI, Request

from .eureka import EurekaRegistry, InstanceInfo, ServiceDiscovery, EurekaClient
from .config import ConfigServerLoader
from .actuator import (
    HealthEndpoint,
    InfoEndpoint,
    PrometheusEndpoint,
    create_default_health_endpoint,
    create_default_info_endpoint,
    create_default_prometheus_endpoint
)
from .integrations.fastapi import FastAPIActuatorIntegration
from .retry import RetryConfig
from .exceptions import SpringReadyException

logger = logging.getLogger(__name__)


class SpringReadyApp:
    """
    Spring-Ready Python Application.

    Provides:
    - Eureka service registration with heartbeat
    - Config Server integration with Eureka discovery
    - Actuator endpoints (/actuator/health, /actuator/info, /actuator/prometheus)
    - FastAPI integration

    Usage:
        from spring_ready import SpringReadyApp
        from fastapi import FastAPI

        app = FastAPI()
        spring_app = SpringReadyApp(app)

        # Your routes here
        @app.get("/")
        def read_root():
            return {"Hello": "World"}
    """

    def __init__(
            self,
            fastapi_app: Optional[FastAPI] = None,
            app_name: Optional[str] = None,
            app_port: Optional[int] = None,
            eureka_servers: Optional[List[str]] = None,
            profile: Optional[str] = None,
            fail_fast: bool = True,
            prefer_ip_address: bool = True,
            instance_ip: Optional[str] = None,
            instance_hostname: Optional[str] = None,
            instance_metadata: Optional[dict] = None,
            secure: bool = False
    ):
        """
        Args:
            fastapi_app: FastAPI application (creates new one if None)
            app_name: Application name (default from env SPRING_APPLICATION_NAME)
            app_port: Application port (default from env APP_PORT or 8080)
            eureka_servers: List of Eureka server URLs (default from env EUREKA_SERVER_URL)
            profile: Active profile (default from env SPRING_PROFILES_ACTIVE or "default")
            fail_fast: If True, fail immediately on startup errors
            prefer_ip_address: Use IP address instead of hostname in Eureka
            instance_ip: Custom IP address to register with Eureka (auto-detected if None)
            instance_hostname: Custom hostname to register with Eureka (auto-detected if None)
            instance_metadata: Additional metadata for Eureka instance
            secure: If True, register with HTTPS URLs (default from env EUREKA_INSTANCE_SECURE)
        """
        # Configuration from environment variables or parameters
        self.app_name = app_name or os.getenv("SPRING_APPLICATION_NAME") or os.getenv("APP_NAME", "python-service")
        self.app_port = app_port or int(os.getenv("APP_PORT", "8080"))
        self.profile = profile or os.getenv("SPRING_PROFILES_ACTIVE", "default")
        self.fail_fast = fail_fast
        self.prefer_ip_address = prefer_ip_address
        self.instance_ip = instance_ip or os.getenv("EUREKA_INSTANCE_IP")
        self.instance_hostname = instance_hostname or os.getenv("EUREKA_INSTANCE_HOSTNAME")
        self.secure = secure or os.getenv("EUREKA_INSTANCE_SECURE", "false").lower() == "true"

        # Testing mode - disables Eureka and Config Server connections
        self.testing_mode = os.getenv("TESTING", "0") == "1"
        if self.testing_mode:
            logger.info("TESTING mode enabled - Eureka and Config Server connections will be disabled")

        # Parse Eureka servers
        if eureka_servers is None:
            eureka_url = os.getenv("EUREKA_SERVER_URL", "http://localhost:8761/eureka/")
            self.eureka_servers = [url.strip() for url in eureka_url.split(",")]
            if eureka_url == "http://localhost:8761/eureka/":
                logger.warning(
                    "Using default Eureka server URL (http://localhost:8761/eureka/). "
                    "If this is not correct, set EUREKA_SERVER_URL environment variable."
                )
        else:
            self.eureka_servers = eureka_servers

        # Log configured Eureka servers prominently
        logger.info(f"Configured Eureka server(s): {', '.join(self.eureka_servers)}")

        # FastAPI app
        self.fastapi_app = fastapi_app or FastAPI(title=self.app_name)

        # Add CORS and actuator middleware BEFORE app starts (must be done during initialization)
        self._setup_cors()
        self._setup_actuator_middleware()

        # Components (initialized in start())
        self.eureka_registry: Optional[EurekaRegistry] = None
        self.service_discovery: Optional[ServiceDiscovery] = None
        self.config_loader: Optional[ConfigServerLoader] = None
        self.health_endpoint: Optional[HealthEndpoint] = None
        self.info_endpoint: Optional[InfoEndpoint] = None
        self.prometheus_endpoint: Optional[PrometheusEndpoint] = None
        self.actuator_integration: Optional[FastAPIActuatorIntegration] = None
        self.httptrace_endpoint: Optional = None  # For HTTP tracing middleware

        # Retry configuration (matching Spring Cloud Config defaults)
        self.retry_config = RetryConfig(
            max_attempts=6,
            initial_interval=1.0,
            max_interval=2.0,
            multiplier=1.1
        )

        # Auto-start on initialization
        self._started = False

    def start(self) -> None:
        """
        Start Spring-Ready application.

        Process:
        1. Register with Eureka (with retry)
        2. Discover Config Server from Eureka
        3. Load configuration from Config Server
        4. Set up actuator endpoints

        Raises:
            SpringReadyException if startup fails and fail_fast=True
        """
        if self._started:
            logger.warning("SpringReadyApp already started")
            return

        logger.info(f"Starting Spring-Ready application: {self.app_name}")

        try:
            # If testing mode is enabled, skip Eureka and Config Server setup
            if self.testing_mode:
                logger.info("Running in TESTING mode - skipping Eureka and Config Server setup")

                # Only set up actuator endpoints
                logger.info("Setting up actuator endpoints...")
                self._setup_actuator_endpoints()

                self._started = True
                logger.info(f"✓ Spring-Ready application started successfully in TESTING mode on port {self.app_port}")
                logger.info(f"  Actuator: http://localhost:{self.app_port}/actuator/health")
                return

            # Step 1: Create Eureka instance info
            instance_info = InstanceInfo.create(
                app_name=self.app_name,
                port=self.app_port,
                secure_port=self.app_port,  # Use same port for HTTPS
                prefer_ip_address=self.prefer_ip_address,
                ip_addr=self.instance_ip,
                host_name=self.instance_hostname,
                metadata=self._get_instance_metadata(),
                secure=self.secure
            )

            # Log instance registration details
            if self.instance_ip:
                logger.info(f"Using custom IP address for Eureka registration: {instance_info.ip_addr}")
            else:
                logger.info(f"Auto-detected IP address for Eureka registration: {instance_info.ip_addr}")

            logger.info(f"Instance will register as: {instance_info.instance_id}")
            if self.secure:
                logger.info(f"Secure mode enabled - registering with HTTPS URLs")

            # Configure FastAPI OpenAPI servers to use the correct service URL
            protocol = "https" if self.secure else "http"
            service_url = f"{protocol}://{instance_info.ip_addr}:{self.app_port}"
            self.fastapi_app.servers = [{"url": service_url, "description": "Service instance"}]
            logger.info(f"Configured OpenAPI server URL: {service_url}")

            # Step 2: Register with Eureka
            logger.info(f"Registering with Eureka: {self.eureka_servers}")
            self.eureka_registry = EurekaRegistry(
                eureka_servers=self.eureka_servers,
                instance_info=instance_info,
                retry_config=self.retry_config,
                fail_fast=self.fail_fast
            )
            self.eureka_registry.start()

            # Step 3: Create service discovery client
            eureka_client = EurekaClient(self.eureka_servers)
            self.service_discovery = ServiceDiscovery(eureka_client)

            # Step 4: Load configuration from Config Server
            logger.info("Loading configuration from Config Server...")
            self.config_loader = ConfigServerLoader(
                app_name=self.app_name,
                profile=self.profile,
                service_discovery=self.service_discovery,
                retry_config=self.retry_config,
                fail_fast=self.fail_fast
            )
            self.config_loader.load_config()

            # Step 5: Set up actuator endpoints
            logger.info("Setting up actuator endpoints...")
            self._setup_actuator_endpoints()

            self._started = True
            logger.info(f"✓ Spring-Ready application started successfully on port {self.app_port}")
            logger.info(f"  Eureka: {self.eureka_servers[0]}")
            logger.info(f"  Actuator: http://localhost:{self.app_port}/actuator/health")

        except Exception as e:
            logger.error(f"Failed to start Spring-Ready application: {e}", exc_info=True)
            if self.fail_fast:
                raise SpringReadyException(f"Startup failed: {e}") from e
            logger.warning("Continuing without full Spring integration due to startup failure")

    def _get_instance_metadata(self) -> dict:
        """Get Eureka instance metadata"""
        metadata = {
            "management.port": str(self.app_port),
            "profile": self.profile,
        }
        return metadata

    def _setup_cors(self) -> None:
        """Set up CORS middleware for actuator endpoints (must be called before app starts)"""
        from fastapi.middleware.cors import CORSMiddleware

        self.fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for Spring Boot Admin compatibility
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )
        logger.info("CORS middleware added for actuator endpoints")

    def _setup_actuator_middleware(self) -> None:
        """Set up Spring Boot Actuator v2 middleware (must be called before app starts)"""
        from .actuator import create_default_httptrace_endpoint

        # Create HTTP trace endpoint first (needed by middleware)
        self.httptrace_endpoint = create_default_httptrace_endpoint()

        @self.fastapi_app.middleware("http")
        async def actuator_middleware(request: Request, call_next):
            import time
            start_time = time.time()

            # Process the request
            response = await call_next(request)

            # Calculate time taken
            time_taken_ms = int((time.time() - start_time) * 1000)

            # Capture HTTP trace (skip actuator endpoints to avoid recursion)
            if not request.url.path.startswith("/actuator"):
                try:
                    # Get request headers
                    headers = dict(request.headers)
                    # Sanitize sensitive headers
                    if "authorization" in headers:
                        headers["authorization"] = "***"
                    if "cookie" in headers:
                        headers["cookie"] = "***"

                    self.httptrace_endpoint.add_trace(
                        method=request.method,
                        uri=str(request.url.path),
                        status=response.status_code,
                        time_taken_ms=time_taken_ms,
                        headers=headers,
                        remote_address=request.client.host if request.client else None
                    )
                except Exception as e:
                    logger.debug(f"Failed to capture HTTP trace: {e}")

            # Set Spring Boot Actuator v2 content type for all actuator endpoints
            if request.url.path.startswith("/actuator"):
                # Only set for JSON responses (not for Prometheus text format)
                if response.headers.get("content-type", "").startswith("application/json"):
                    response.headers["content-type"] = "application/vnd.spring-boot.actuator.v2+json;charset=UTF-8"

            return response

        logger.info("Spring Boot Actuator v2 middleware enabled (content-type + HTTP tracing)")

    def _setup_actuator_endpoints(self) -> None:
        """Set up Spring Boot Actuator endpoints"""
        from .actuator import create_default_logfile_endpoint, create_default_refresh_endpoint

        # Create endpoints
        self.health_endpoint = create_default_health_endpoint()
        self.info_endpoint = create_default_info_endpoint(
            app_name=self.app_name,
            app_version=os.getenv("APP_VERSION", "unknown")
        )
        self.prometheus_endpoint = create_default_prometheus_endpoint()

        # Create logfile endpoint (will use LOG_FILE_PATH env var if set)
        logfile_endpoint = create_default_logfile_endpoint()

        # Create refresh endpoint with config loader
        refresh_endpoint = create_default_refresh_endpoint(
            config_loader=self.config_loader
        )

        # Add Eureka health check
        if self.eureka_registry:
            self.health_endpoint.add_check(
                "eureka",
                lambda: self.eureka_registry._registered
            )

        # Build base URL for actuator discovery
        # Try to use instance_ip if available, otherwise use localhost
        # In testing mode, always use localhost since we don't connect to Eureka
        if self.testing_mode:
            host = "localhost"
        else:
            host = self.instance_ip if self.instance_ip else "localhost"
        protocol = "https" if self.secure else "http"
        base_url = f"{protocol}://{host}:{self.app_port}"

        # Integrate with FastAPI (CORS and middleware already set up in __init__)
        self.actuator_integration = FastAPIActuatorIntegration(
            app=self.fastapi_app,
            base_url=base_url,
            health_endpoint=self.health_endpoint,
            info_endpoint=self.info_endpoint,
            prometheus_endpoint=self.prometheus_endpoint,
            httptrace_endpoint=self.httptrace_endpoint,  # Use the one created in middleware
            logfile_endpoint=logfile_endpoint,
            refresh_endpoint=refresh_endpoint,
            enable_cors=False  # Already added in __init__
        )

    def shutdown(self) -> None:
        """
        Gracefully shutdown the application.
        Deregisters from Eureka.
        """
        logger.info("Shutting down Spring-Ready application...")

        if self.eureka_registry:
            self.eureka_registry.shutdown()

        logger.info("Shutdown complete")

    @property
    def app(self) -> FastAPI:
        """Get FastAPI application"""
        return self.fastapi_app

    # Prometheus metrics convenience methods
    def create_counter(self, name: str, description: str, labels: Optional[List[str]] = None):
        """
        Create a Prometheus Counter metric.

        Args:
            name: Metric name (use snake_case)
            description: Human-readable description
            labels: Optional list of label names

        Returns:
            Counter instance or None if prometheus_client not available

        Example:
            request_counter = spring_app.create_counter(
                'http_requests_total',
                'Total HTTP requests',
                ['method', 'endpoint']
            )
            request_counter.labels(method='GET', endpoint='/api/users').inc()
        """
        if not self.prometheus_endpoint:
            logger.warning("Cannot create counter: Prometheus endpoint not initialized")
            return None
        return self.prometheus_endpoint.create_counter(name, description, labels)

    def create_gauge(self, name: str, description: str, labels: Optional[List[str]] = None):
        """
        Create a Prometheus Gauge metric.

        Args:
            name: Metric name (use snake_case)
            description: Human-readable description
            labels: Optional list of label names

        Returns:
            Gauge instance or None if prometheus_client not available

        Example:
            queue_size = spring_app.create_gauge(
                'queue_size',
                'Current queue size',
                ['queue_name']
            )
            queue_size.labels(queue_name='processing').set(42)
        """
        if not self.prometheus_endpoint:
            logger.warning("Cannot create gauge: Prometheus endpoint not initialized")
            return None
        return self.prometheus_endpoint.create_gauge(name, description, labels)

    def create_histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None
    ):
        """
        Create a Prometheus Histogram metric.

        Args:
            name: Metric name (use snake_case)
            description: Human-readable description
            labels: Optional list of label names
            buckets: Optional bucket boundaries

        Returns:
            Histogram instance or None if prometheus_client not available

        Example:
            request_duration = spring_app.create_histogram(
                'request_duration_seconds',
                'HTTP request duration in seconds',
                ['endpoint']
            )
            with request_duration.labels(endpoint='/api/users').time():
                process_request()
        """
        if not self.prometheus_endpoint:
            logger.warning("Cannot create histogram: Prometheus endpoint not initialized")
            return None
        return self.prometheus_endpoint.create_histogram(name, description, labels, buckets)

    def create_summary(self, name: str, description: str, labels: Optional[List[str]] = None):
        """
        Create a Prometheus Summary metric.

        Args:
            name: Metric name (use snake_case)
            description: Human-readable description
            labels: Optional list of label names

        Returns:
            Summary instance or None if prometheus_client not available

        Example:
            request_latency = spring_app.create_summary(
                'request_latency_seconds',
                'Request latency in seconds',
                ['service']
            )
            with request_latency.labels(service='api').time():
                process_request()
        """
        if not self.prometheus_endpoint:
            logger.warning("Cannot create summary: Prometheus endpoint not initialized")
            return None
        return self.prometheus_endpoint.create_summary(name, description, labels)


# Convenience function for simple use case
def create_spring_ready_app(
        app_name: Optional[str] = None,
        app_port: Optional[int] = None,
        **kwargs
) -> SpringReadyApp:
    """
    Create and start a Spring-Ready FastAPI application.

    Args:
        app_name: Application name
        app_port: Application port
        **kwargs: Additional arguments for SpringReadyApp

    Returns:
        SpringReadyApp instance with FastAPI app started
    """
    spring_app = SpringReadyApp(
        app_name=app_name,
        app_port=app_port,
        **kwargs
    )
    spring_app.start()
    return spring_app