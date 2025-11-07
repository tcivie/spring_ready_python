"""
Prometheus metrics endpoint.
Exposes metrics in Prometheus format at /actuator/prometheus.
"""

import logging
from typing import Optional, List, Union
import psutil
import time
import threading

logger = logging.getLogger(__name__)

# Check if prometheus_client is available
try:
    from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
    from prometheus_client import Counter, Gauge, Histogram, Summary
    from prometheus_client import ProcessCollector, PlatformCollector

    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    logger.warning(
        "prometheus_client not installed. "
        "Install it with: pip install prometheus-client"
    )

# Track start time for uptime metric
_start_time = time.time()


class PrometheusEndpoint:
    """
    Prometheus metrics endpoint.

    Provides metrics in Prometheus exposition format.
    Automatically includes process and platform metrics.
    """

    def __init__(self, registry: Optional["CollectorRegistry"] = None, enable_default_metrics: bool = True):
        """
        Args:
            registry: Prometheus registry (creates default if None)
            enable_default_metrics: If True, register default system metrics (CPU, memory, threads, etc.)
        """
        if not HAS_PROMETHEUS:
            logger.error("Cannot create PrometheusEndpoint: prometheus_client not installed")
            self.registry = None
            return

        self.registry = registry or CollectorRegistry()

        # Add default collectors (process and platform metrics)
        try:
            ProcessCollector(registry=self.registry)
            PlatformCollector(registry=self.registry)
        except Exception as e:
            logger.warning(f"Failed to register default collectors: {e}")

        # Register default system metrics if enabled
        if enable_default_metrics:
            self._register_default_system_metrics()

    def get_metrics(self) -> bytes:
        """
        Get metrics in Prometheus format.

        Returns:
            Metrics as bytes in Prometheus exposition format
        """
        if not HAS_PROMETHEUS or not self.registry:
            return b"# Prometheus client not installed\n"

        try:
            return generate_latest(self.registry)
        except Exception as e:
            logger.error(f"Failed to generate Prometheus metrics: {e}")
            return f"# Error generating metrics: {e}\n".encode('utf-8')

    @property
    def content_type(self) -> str:
        """Get Prometheus content type"""
        if HAS_PROMETHEUS:
            return CONTENT_TYPE_LATEST
        return "text/plain; charset=utf-8"

    def _register_default_system_metrics(self) -> None:
        """
        Register default system metrics in Prometheus format.

        Exports all Spring Boot Actuator-style metrics to Prometheus:
        - System CPU usage and count
        - Process uptime and start time
        - Process CPU and memory usage
        - Python thread counts
        - Python garbage collection stats
        """
        if not HAS_PROMETHEUS or not self.registry:
            return

        try:
            # System CPU metrics
            system_cpu_usage = Gauge(
                'system_cpu_usage',
                'System CPU usage (0.0-1.0)',
                registry=self.registry
            )
            system_cpu_usage.set_function(lambda: psutil.cpu_percent(interval=0) / 100.0)

            system_cpu_count = Gauge(
                'system_cpu_count',
                'Number of CPU cores',
                registry=self.registry
            )
            system_cpu_count.set_function(lambda: psutil.cpu_count())

            # Process uptime and start time
            process_uptime = Gauge(
                'process_uptime_seconds',
                'Application uptime in seconds',
                registry=self.registry
            )
            process_uptime.set_function(lambda: time.time() - _start_time)

            process_start_time = Gauge(
                'process_start_time_seconds',
                'Application start time (epoch seconds)',
                registry=self.registry
            )
            process_start_time.set(_start_time)

            # Process CPU usage
            process_cpu_usage = Gauge(
                'process_cpu_usage',
                'Process CPU usage (0.0-1.0)',
                registry=self.registry
            )
            current_process = psutil.Process()
            process_cpu_usage.set_function(lambda: current_process.cpu_percent(interval=0) / 100.0)

            # Process memory usage
            process_memory_virtual = Gauge(
                'process_memory_virtual_bytes',
                'Virtual memory in bytes',
                registry=self.registry
            )
            process_memory_virtual.set_function(lambda: current_process.memory_info().vms)

            process_memory_physical = Gauge(
                'process_memory_physical_bytes',
                'Physical memory (RSS) in bytes',
                registry=self.registry
            )
            process_memory_physical.set_function(lambda: current_process.memory_info().rss)

            # Python thread counts
            python_threads_total = Gauge(
                'python_threads_total',
                'Total number of threads',
                registry=self.registry
            )
            python_threads_total.set_function(lambda: threading.active_count())

            python_threads_daemon = Gauge(
                'python_threads_daemon',
                'Number of daemon threads',
                registry=self.registry
            )
            def count_daemon_threads():
                return sum(1 for t in threading.enumerate() if t.daemon)
            python_threads_daemon.set_function(count_daemon_threads)

            # Python garbage collection stats
            import gc
            python_gc_objects = Gauge(
                'python_gc_objects',
                'Number of objects tracked by GC',
                ['generation'],
                registry=self.registry
            )
            for generation in range(3):
                python_gc_objects.labels(generation=str(generation)).set_function(
                    lambda g=generation: gc.get_count()[g]
                )

            logger.info("Registered default system metrics for Prometheus")

        except Exception as e:
            logger.warning(f"Failed to register default system metrics: {e}")

    def create_counter(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Optional["Counter"]:
        """
        Create a Prometheus Counter metric.

        Counters are for cumulative metrics that only increase (e.g., request count, errors).

        Args:
            name: Metric name (use snake_case, e.g., 'http_requests_total')
            description: Human-readable description
            labels: Optional list of label names (e.g., ['method', 'status'])

        Returns:
            Counter instance or None if prometheus_client not available

        Example:
            request_counter = prometheus.create_counter(
                'http_requests_total',
                'Total HTTP requests',
                ['method', 'endpoint']
            )
            request_counter.labels(method='GET', endpoint='/api/users').inc()
        """
        if not HAS_PROMETHEUS or not self.registry:
            logger.warning("Cannot create counter: prometheus_client not available")
            return None

        try:
            return Counter(name, description, labels or [], registry=self.registry)
        except Exception as e:
            logger.error(f"Failed to create counter '{name}': {e}")
            return None

    def create_gauge(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Optional["Gauge"]:
        """
        Create a Prometheus Gauge metric.

        Gauges are for metrics that can go up or down (e.g., temperature, memory usage).

        Args:
            name: Metric name (use snake_case, e.g., 'queue_size')
            description: Human-readable description
            labels: Optional list of label names (e.g., ['queue_name'])

        Returns:
            Gauge instance or None if prometheus_client not available

        Example:
            queue_size = prometheus.create_gauge(
                'queue_size',
                'Current queue size',
                ['queue_name']
            )
            queue_size.labels(queue_name='processing').set(42)
        """
        if not HAS_PROMETHEUS or not self.registry:
            logger.warning("Cannot create gauge: prometheus_client not available")
            return None

        try:
            return Gauge(name, description, labels or [], registry=self.registry)
        except Exception as e:
            logger.error(f"Failed to create gauge '{name}': {e}")
            return None

    def create_histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None
    ) -> Optional["Histogram"]:
        """
        Create a Prometheus Histogram metric.

        Histograms track distributions of values (e.g., request duration, response size).

        Args:
            name: Metric name (use snake_case, e.g., 'request_duration_seconds')
            description: Human-readable description
            labels: Optional list of label names (e.g., ['endpoint'])
            buckets: Optional bucket boundaries (default: [.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0])

        Returns:
            Histogram instance or None if prometheus_client not available

        Example:
            request_duration = prometheus.create_histogram(
                'request_duration_seconds',
                'HTTP request duration in seconds',
                ['endpoint']
            )
            with request_duration.labels(endpoint='/api/users').time():
                process_request()
        """
        if not HAS_PROMETHEUS or not self.registry:
            logger.warning("Cannot create histogram: prometheus_client not available")
            return None

        try:
            kwargs = {"registry": self.registry}
            if buckets is not None:
                kwargs["buckets"] = buckets
            return Histogram(name, description, labels or [], **kwargs)
        except Exception as e:
            logger.error(f"Failed to create histogram '{name}': {e}")
            return None

    def create_summary(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Optional["Summary"]:
        """
        Create a Prometheus Summary metric.

        Summaries track distributions similar to histograms but calculate quantiles.

        Args:
            name: Metric name (use snake_case, e.g., 'request_latency_seconds')
            description: Human-readable description
            labels: Optional list of label names (e.g., ['service'])

        Returns:
            Summary instance or None if prometheus_client not available

        Example:
            request_latency = prometheus.create_summary(
                'request_latency_seconds',
                'Request latency in seconds',
                ['service']
            )
            with request_latency.labels(service='api').time():
                process_request()
        """
        if not HAS_PROMETHEUS or not self.registry:
            logger.warning("Cannot create summary: prometheus_client not available")
            return None

        try:
            return Summary(name, description, labels or [], registry=self.registry)
        except Exception as e:
            logger.error(f"Failed to create summary '{name}': {e}")
            return None


def create_default_prometheus_endpoint() -> PrometheusEndpoint:
    """
    Create Prometheus endpoint with default registry.

    Returns:
        PrometheusEndpoint with process and platform collectors
    """
    return PrometheusEndpoint()