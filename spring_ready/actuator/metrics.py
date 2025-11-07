"""
Actuator Metrics Endpoint.
Lists available metrics and retrieves individual metric values.
"""

import psutil
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


_start_time = time.time()


@dataclass
class MetricMeasurement:
    """Single measurement of a metric"""
    statistic: str  # VALUE, TOTAL, COUNT, etc.
    value: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statistic": self.statistic,
            "value": self.value
        }


@dataclass
class MetricTag:
    """Available tag for filtering metrics"""
    tag: str
    values: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag": self.tag,
            "values": self.values
        }


@dataclass
class Metric:
    """Complete metric with measurements and tags"""
    name: str
    description: str
    baseUnit: Optional[str] = None
    measurements: List[MetricMeasurement] = field(default_factory=list)
    availableTags: List[MetricTag] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "description": self.description,
            "measurements": [m.to_dict() for m in self.measurements],
            "availableTags": [t.to_dict() for t in self.availableTags]
        }
        if self.baseUnit:
            result["baseUnit"] = self.baseUnit
        return result


class MetricsEndpoint:
    """
    Metrics endpoint for Spring Boot Actuator compatibility.

    Provides:
    - List of available metric names
    - Individual metric retrieval with measurements
    - Tag-based filtering

    Note: This is for monitoring/debugging, not production metrics scraping.
    Use Prometheus endpoint for production metrics collection.
    """

    def __init__(self):
        """Initialize metrics endpoint"""
        self.custom_metrics: Dict[str, Metric] = {}

    def get_metric_names(self) -> Dict[str, List[str]]:
        """
        Get list of all available metric names.

        Returns:
            Dictionary with "names" key containing list of metric names
        """
        names = []

        # System metrics
        names.extend([
            "system.cpu.usage",
            "system.cpu.count",
            "process.uptime",
            "process.start.time",
            "process.cpu.usage",
            "process.virtual.memory",
            "process.physical.memory",
            "python.threads.total",
            "python.threads.daemon",
            "python.gc.count"
        ])

        # Custom metrics
        names.extend(self.custom_metrics.keys())

        return {"names": sorted(names)}

    def get_metric(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Get individual metric by name.

        Args:
            name: Metric name
            tags: Optional tag filters (e.g., {"area": "heap"})

        Returns:
            Metric details with measurements or None if not found
        """
        # Check custom metrics first
        if name in self.custom_metrics:
            metric = self.custom_metrics[name]
            return metric.to_dict()

        # System metrics
        if name == "system.cpu.usage":
            # Get CPU percentage as a fraction (0.0 to 1.0) for Spring Boot compatibility
            cpu_percent = psutil.cpu_percent(interval=0.1) / 100.0
            return Metric(
                name="system.cpu.usage",
                description="The recent CPU usage of the system",
                baseUnit="percent",
                measurements=[
                    MetricMeasurement("VALUE", cpu_percent)
                ]
            ).to_dict()

        elif name == "system.cpu.count":
            return Metric(
                name="system.cpu.count",
                description="The number of processors available to the process",
                baseUnit="cores",
                measurements=[
                    MetricMeasurement("VALUE", psutil.cpu_count())
                ]
            ).to_dict()

        elif name == "process.uptime":
            uptime = time.time() - _start_time
            return Metric(
                name="process.uptime",
                description="The uptime of the application",
                baseUnit="seconds",
                measurements=[
                    MetricMeasurement("VALUE", uptime)
                ]
            ).to_dict()

        elif name == "process.start.time":
            return Metric(
                name="process.start.time",
                description="Start time of the process",
                baseUnit="epoch_seconds",
                measurements=[
                    MetricMeasurement("VALUE", _start_time)
                ]
            ).to_dict()

        elif name == "process.cpu.usage":
            process = psutil.Process()
            # Get CPU percentage as a fraction (0.0 to 1.0) for Spring Boot compatibility
            cpu_percent = process.cpu_percent(interval=0.1) / 100.0
            return Metric(
                name="process.cpu.usage",
                description="The recent CPU usage for the process",
                baseUnit="percent",
                measurements=[
                    MetricMeasurement("VALUE", cpu_percent)
                ]
            ).to_dict()

        elif name == "process.virtual.memory":
            process = psutil.Process()
            mem_info = process.memory_info()
            return Metric(
                name="process.virtual.memory",
                description="Virtual memory used by the process",
                baseUnit="bytes",
                measurements=[
                    MetricMeasurement("VALUE", mem_info.vms)
                ]
            ).to_dict()

        elif name == "process.physical.memory":
            process = psutil.Process()
            mem_info = process.memory_info()
            return Metric(
                name="process.physical.memory",
                description="Physical memory (RSS) used by the process",
                baseUnit="bytes",
                measurements=[
                    MetricMeasurement("VALUE", mem_info.rss)
                ]
            ).to_dict()

        elif name == "python.threads.total":
            import threading
            return Metric(
                name="python.threads.total",
                description="Total number of threads",
                measurements=[
                    MetricMeasurement("VALUE", threading.active_count())
                ]
            ).to_dict()

        elif name == "python.threads.daemon":
            import threading
            daemon_count = sum(1 for t in threading.enumerate() if t.daemon)
            return Metric(
                name="python.threads.daemon",
                description="Number of daemon threads",
                measurements=[
                    MetricMeasurement("VALUE", daemon_count)
                ]
            ).to_dict()

        elif name == "python.gc.count":
            import gc
            counts = gc.get_count()
            return Metric(
                name="python.gc.count",
                description="Number of garbage collection objects",
                measurements=[
                    MetricMeasurement("GENERATION_0", counts[0]),
                    MetricMeasurement("GENERATION_1", counts[1]),
                    MetricMeasurement("GENERATION_2", counts[2])
                ],
                availableTags=[
                    MetricTag("generation", ["0", "1", "2"])
                ]
            ).to_dict()

        return None

    def register_custom_metric(self, metric: Metric) -> None:
        """
        Register a custom metric.

        Args:
            metric: Metric to register
        """
        self.custom_metrics[metric.name] = metric


def create_default_metrics_endpoint() -> MetricsEndpoint:
    """
    Create metrics endpoint with default system metrics.

    Returns:
        MetricsEndpoint instance
    """
    return MetricsEndpoint()
