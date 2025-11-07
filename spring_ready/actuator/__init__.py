"""Spring Boot Actuator-compatible endpoints"""

from .health import HealthEndpoint, HealthIndicator, HealthStatus, create_default_health_endpoint
from .info import InfoEndpoint, create_default_info_endpoint
from .prometheus import PrometheusEndpoint, create_default_prometheus_endpoint
from .discovery import ActuatorDiscoveryEndpoint, create_default_discovery_endpoint
from .metrics import MetricsEndpoint, create_default_metrics_endpoint
from .env import EnvEndpoint, create_default_env_endpoint
from .loggers import LoggersEndpoint, create_default_loggers_endpoint
from .mappings import MappingsEndpoint, create_default_mappings_endpoint
from .threaddump import ThreadDumpEndpoint, create_default_threaddump_endpoint
from .httptrace import (
    HttpTraceEndpoint,
    HttpExchangesEndpoint,
    create_default_httptrace_endpoint,
    create_default_httpexchanges_endpoint
)
from .logfile import LogfileEndpoint, create_default_logfile_endpoint
from .refresh import RefreshEndpoint, create_default_refresh_endpoint
from .beans import BeansEndpoint, create_default_beans_endpoint
from .configprops import ConfigPropsEndpoint, create_default_configprops_endpoint
from .scheduledtasks import ScheduledTasksEndpoint, create_default_scheduledtasks_endpoint
from .heapdump import HeapdumpEndpoint, create_default_heapdump_endpoint
from .caches import CachesEndpoint, create_default_caches_endpoint
from .auditevents import AuditEventsEndpoint, create_default_auditevents_endpoint

__all__ = [
    "HealthEndpoint",
    "HealthIndicator",
    "HealthStatus",
    "create_default_health_endpoint",
    "InfoEndpoint",
    "create_default_info_endpoint",
    "PrometheusEndpoint",
    "create_default_prometheus_endpoint",
    "ActuatorDiscoveryEndpoint",
    "create_default_discovery_endpoint",
    "MetricsEndpoint",
    "create_default_metrics_endpoint",
    "EnvEndpoint",
    "create_default_env_endpoint",
    "LoggersEndpoint",
    "create_default_loggers_endpoint",
    "MappingsEndpoint",
    "create_default_mappings_endpoint",
    "ThreadDumpEndpoint",
    "create_default_threaddump_endpoint",
    "HttpTraceEndpoint",
    "HttpExchangesEndpoint",
    "create_default_httptrace_endpoint",
    "create_default_httpexchanges_endpoint",
    "LogfileEndpoint",
    "create_default_logfile_endpoint",
    "RefreshEndpoint",
    "create_default_refresh_endpoint",
    "BeansEndpoint",
    "create_default_beans_endpoint",
    "ConfigPropsEndpoint",
    "create_default_configprops_endpoint",
    "ScheduledTasksEndpoint",
    "create_default_scheduledtasks_endpoint",
    "HeapdumpEndpoint",
    "create_default_heapdump_endpoint",
    "CachesEndpoint",
    "create_default_caches_endpoint",
    "AuditEventsEndpoint",
    "create_default_auditevents_endpoint",
]