"""
FastAPI integration for Spring-Ready Python.
Adds actuator endpoints and integrates with Eureka/Config Server.
"""

import logging
from typing import Optional
from fastapi import FastAPI, Response, Request, Body
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from ..actuator import (
    HealthEndpoint,
    InfoEndpoint,
    PrometheusEndpoint,
    ActuatorDiscoveryEndpoint,
    MetricsEndpoint,
    EnvEndpoint,
    LoggersEndpoint,
    MappingsEndpoint,
    ThreadDumpEndpoint,
    HttpTraceEndpoint,
    HttpExchangesEndpoint,
    LogfileEndpoint,
    RefreshEndpoint,
    BeansEndpoint,
    ConfigPropsEndpoint,
    ScheduledTasksEndpoint,
    HeapdumpEndpoint,
    CachesEndpoint,
    AuditEventsEndpoint,
    create_default_health_endpoint,
    create_default_info_endpoint,
    create_default_prometheus_endpoint,
    create_default_discovery_endpoint,
    create_default_metrics_endpoint,
    create_default_env_endpoint,
    create_default_loggers_endpoint,
    create_default_mappings_endpoint,
    create_default_threaddump_endpoint,
    create_default_httptrace_endpoint,
    create_default_httpexchanges_endpoint,
    create_default_logfile_endpoint,
    create_default_refresh_endpoint,
    create_default_beans_endpoint,
    create_default_configprops_endpoint,
    create_default_scheduledtasks_endpoint,
    create_default_heapdump_endpoint,
    create_default_caches_endpoint,
    create_default_auditevents_endpoint
)

logger = logging.getLogger(__name__)


class FastAPIActuatorIntegration:
    """
    Integrates Spring Boot Actuator endpoints with FastAPI.

    Adds the following endpoints:
    - GET /actuator - Discovery endpoint with HAL JSON
    - GET /actuator/health - Health status
    - GET /actuator/info - Application information
    - GET /actuator/prometheus - Prometheus metrics
    - GET /actuator/metrics - Metrics list
    - GET /actuator/metrics/{name} - Individual metric
    - GET /actuator/env - Environment variables
    - GET /actuator/env/{property} - Single property
    - GET /actuator/loggers - All loggers
    - GET /actuator/loggers/{name} - Single logger
    - POST /actuator/loggers/{name} - Set logger level
    - GET /actuator/mappings - Request mappings
    - GET /actuator/threaddump - Thread dump
    """

    def __init__(
            self,
            app: FastAPI,
            base_url: str,
            health_endpoint: Optional[HealthEndpoint] = None,
            info_endpoint: Optional[InfoEndpoint] = None,
            prometheus_endpoint: Optional[PrometheusEndpoint] = None,
            discovery_endpoint: Optional[ActuatorDiscoveryEndpoint] = None,
            metrics_endpoint: Optional[MetricsEndpoint] = None,
            env_endpoint: Optional[EnvEndpoint] = None,
            loggers_endpoint: Optional[LoggersEndpoint] = None,
            mappings_endpoint: Optional[MappingsEndpoint] = None,
            threaddump_endpoint: Optional[ThreadDumpEndpoint] = None,
            httptrace_endpoint: Optional[HttpTraceEndpoint] = None,
            httpexchanges_endpoint: Optional[HttpExchangesEndpoint] = None,
            logfile_endpoint: Optional[LogfileEndpoint] = None,
            refresh_endpoint: Optional[RefreshEndpoint] = None,
            beans_endpoint: Optional[BeansEndpoint] = None,
            configprops_endpoint: Optional[ConfigPropsEndpoint] = None,
            scheduledtasks_endpoint: Optional[ScheduledTasksEndpoint] = None,
            heapdump_endpoint: Optional[HeapdumpEndpoint] = None,
            caches_endpoint: Optional[CachesEndpoint] = None,
            auditevents_endpoint: Optional[AuditEventsEndpoint] = None,
            enable_cors: bool = True
    ):
        """
        Args:
            app: FastAPI application
            base_url: Base URL for the application (e.g., "http://localhost:8080")
            health_endpoint: Health endpoint (creates default if None)
            info_endpoint: Info endpoint (creates default if None)
            prometheus_endpoint: Prometheus endpoint (creates default if None)
            discovery_endpoint: Discovery endpoint (creates default if None)
            metrics_endpoint: Metrics endpoint (creates default if None)
            env_endpoint: Environment endpoint (creates default if None)
            loggers_endpoint: Loggers endpoint (creates default if None)
            mappings_endpoint: Mappings endpoint (creates default if None)
            threaddump_endpoint: Thread dump endpoint (creates default if None)
            httptrace_endpoint: HTTP trace endpoint (creates default if None)
            httpexchanges_endpoint: HTTP exchanges endpoint (creates default if None)
            logfile_endpoint: Logfile endpoint (creates default if None)
            refresh_endpoint: Refresh endpoint (creates default if None)
            enable_cors: Whether to enable CORS for actuator endpoints (default: True)
        """
        self.app = app
        self.base_url = base_url
        self.health_endpoint = health_endpoint or create_default_health_endpoint()
        self.info_endpoint = info_endpoint or create_default_info_endpoint()
        self.prometheus_endpoint = prometheus_endpoint or create_default_prometheus_endpoint()
        self.discovery_endpoint = discovery_endpoint or create_default_discovery_endpoint(base_url)
        self.metrics_endpoint = metrics_endpoint or create_default_metrics_endpoint()
        self.env_endpoint = env_endpoint or create_default_env_endpoint()
        self.loggers_endpoint = loggers_endpoint or create_default_loggers_endpoint()
        self.mappings_endpoint = mappings_endpoint or create_default_mappings_endpoint(app)
        self.threaddump_endpoint = threaddump_endpoint or create_default_threaddump_endpoint()
        self.httptrace_endpoint = httptrace_endpoint or create_default_httptrace_endpoint()
        self.httpexchanges_endpoint = httpexchanges_endpoint or create_default_httpexchanges_endpoint()
        self.logfile_endpoint = logfile_endpoint or create_default_logfile_endpoint()
        self.refresh_endpoint = refresh_endpoint or create_default_refresh_endpoint()
        self.beans_endpoint = beans_endpoint or create_default_beans_endpoint(app)
        self.configprops_endpoint = configprops_endpoint or create_default_configprops_endpoint()
        self.scheduledtasks_endpoint = scheduledtasks_endpoint or create_default_scheduledtasks_endpoint()
        self.heapdump_endpoint = heapdump_endpoint or create_default_heapdump_endpoint()
        self.caches_endpoint = caches_endpoint or create_default_caches_endpoint()
        self.auditevents_endpoint = auditevents_endpoint or create_default_auditevents_endpoint()

        # NOTE: Middleware is now added in core.py during __init__ (before app starts)
        # This avoids the "Cannot add middleware after startup" error

        if enable_cors:
            self._enable_cors()

        self._register_endpoints()

    def _enable_cors(self) -> None:
        """Enable CORS for actuator endpoints"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for Spring Boot Admin compatibility
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
            allow_headers=["*"],
        )
        logger.info("CORS enabled for actuator endpoints")

    def _add_options_handler(self, path: str) -> None:
        """Add OPTIONS handler for a specific path to support CORS preflight"""
        @self.app.options(path, tags=["actuator"], include_in_schema=False)
        async def options_handler():
            """Handle OPTIONS preflight request"""
            return Response(status_code=200)

    def _register_endpoints(self) -> None:
        """Register actuator endpoints with FastAPI"""

        # Discovery endpoint - lists all available actuator endpoints
        @self.app.get("/actuator", tags=["actuator"], include_in_schema=False)
        async def actuator_discovery():
            """Actuator discovery endpoint with HAL JSON"""
            return JSONResponse(content=self.discovery_endpoint.to_dict())

        self._add_options_handler("/actuator")

        # Health endpoint
        @self.app.get("/actuator/health", tags=["actuator"], include_in_schema=False)
        async def health():
            """Health check endpoint"""
            health_data = self.health_endpoint.check()
            status_code = 503 if health_data["status"] == "DOWN" else 200
            return JSONResponse(content=health_data, status_code=status_code)

        self._add_options_handler("/actuator/health")

        # Info endpoint
        @self.app.get("/actuator/info", tags=["actuator"], include_in_schema=False)
        async def info():
            """Application info endpoint"""
            return JSONResponse(content=self.info_endpoint.get_info())

        self._add_options_handler("/actuator/info")

        # Prometheus endpoint
        @self.app.get("/actuator/prometheus", tags=["actuator"], include_in_schema=False)
        async def prometheus():
            """Prometheus metrics endpoint"""
            metrics = self.prometheus_endpoint.get_metrics()
            return Response(
                content=metrics,
                media_type=self.prometheus_endpoint.content_type
            )

        self._add_options_handler("/actuator/prometheus")

        # Metrics endpoint - list all metrics
        @self.app.get("/actuator/metrics", tags=["actuator"], include_in_schema=False)
        async def metrics_list():
            """List all available metrics"""
            return JSONResponse(content=self.metrics_endpoint.get_metric_names())

        self._add_options_handler("/actuator/metrics")

        # Metrics endpoint - get individual metric
        @self.app.get("/actuator/metrics/{metric_name}", tags=["actuator"], include_in_schema=False)
        async def metrics_detail(metric_name: str):
            """Get individual metric details"""
            metric = self.metrics_endpoint.get_metric(metric_name)
            if metric is None:
                return JSONResponse(
                    content={"error": f"Metric '{metric_name}' not found"},
                    status_code=404
                )
            return JSONResponse(content=metric)

        # Environment endpoint - all environment variables
        @self.app.get("/actuator/env", tags=["actuator"], include_in_schema=False)
        async def env_all():
            """Get all environment variables (sanitized)"""
            return JSONResponse(content=self.env_endpoint.get_environment())

        self._add_options_handler("/actuator/env")

        # Environment endpoint - single property
        @self.app.get("/actuator/env/{property_name:path}", tags=["actuator"], include_in_schema=False)
        async def env_property(property_name: str):
            """Get single environment property"""
            prop = self.env_endpoint.get_property(property_name)
            if prop is None:
                return JSONResponse(
                    content={"error": f"Property '{property_name}' not found"},
                    status_code=404
                )
            return JSONResponse(content=prop)

        # Loggers endpoint - all loggers
        @self.app.get("/actuator/loggers", tags=["actuator"], include_in_schema=False)
        async def loggers_all():
            """Get all loggers"""
            return JSONResponse(content=self.loggers_endpoint.get_all_loggers())

        self._add_options_handler("/actuator/loggers")

        # Loggers endpoint - single logger
        @self.app.get("/actuator/loggers/{logger_name:path}", tags=["actuator"], include_in_schema=False)
        async def loggers_single(logger_name: str):
            """Get single logger"""
            logger_info = self.loggers_endpoint.get_logger(logger_name)
            if logger_info is None:
                return JSONResponse(
                    content={"error": f"Logger '{logger_name}' not found"},
                    status_code=404
                )
            return JSONResponse(content=logger_info)

        # Loggers endpoint - set logger level
        @self.app.post("/actuator/loggers/{logger_name:path}", tags=["actuator"], include_in_schema=False)
        async def loggers_set_level(logger_name: str, body: dict = Body(...)):
            """Set logger level"""
            configured_level = body.get("configuredLevel")
            success = self.loggers_endpoint.set_logger_level(logger_name, configured_level)
            if not success:
                return JSONResponse(
                    content={"error": f"Failed to set logger level for '{logger_name}'"},
                    status_code=400
                )
            return Response(status_code=204)

        # Mappings endpoint
        @self.app.get("/actuator/mappings", tags=["actuator"], include_in_schema=False)
        async def mappings():
            """Get request mappings"""
            return JSONResponse(content=self.mappings_endpoint.get_mappings())

        self._add_options_handler("/actuator/mappings")

        # Thread dump endpoint
        @self.app.get("/actuator/threaddump", tags=["actuator"], include_in_schema=False)
        async def threaddump():
            """Get thread dump"""
            return JSONResponse(content=self.threaddump_endpoint.get_thread_dump())

        self._add_options_handler("/actuator/threaddump")

        # HTTP Trace endpoint (older Spring Boot versions)
        @self.app.get("/actuator/httptrace", tags=["actuator"], include_in_schema=False)
        async def httptrace():
            """Get HTTP trace (request/response history)"""
            return JSONResponse(content=self.httptrace_endpoint.get_traces())

        self._add_options_handler("/actuator/httptrace")

        # HTTP Exchanges endpoint (newer Spring Boot 2.2+)
        @self.app.get("/actuator/httpexchanges", tags=["actuator"], include_in_schema=False)
        async def httpexchanges():
            """Get HTTP exchanges (request/response history)"""
            return JSONResponse(content=self.httpexchanges_endpoint.get_exchanges())

        self._add_options_handler("/actuator/httpexchanges")

        # Dump/Trace endpoint (alias for threaddump, some Spring Boot Admin versions use this)
        @self.app.get("/actuator/dump", tags=["actuator"], include_in_schema=False)
        async def dump():
            """Get thread dump (alias)"""
            return JSONResponse(content=self.threaddump_endpoint.get_thread_dump())

        self._add_options_handler("/actuator/dump")

        # Trace endpoint (simple trace, for older versions)
        @self.app.get("/actuator/trace", tags=["actuator"], include_in_schema=False)
        async def trace():
            """Get trace information"""
            return JSONResponse(content=self.httptrace_endpoint.get_traces())

        self._add_options_handler("/actuator/trace")

        # Logfile endpoint - returns application log file
        @self.app.get("/actuator/logfile", tags=["actuator"], include_in_schema=False)
        async def logfile(request: Request):
            """Get application log file"""
            # Check if logfile is available
            if not self.logfile_endpoint.is_available():
                return JSONResponse(
                    content={"error": "Log file not configured or not available"},
                    status_code=404
                )

            # Get Range header if present
            range_header = request.headers.get("Range")

            # Get log file content
            content, content_range, status_code = self.logfile_endpoint.get_logfile(range_header)

            if status_code == 404:
                return JSONResponse(
                    content={"error": "Log file not found"},
                    status_code=404
                )
            elif status_code == 416:
                return Response(status_code=416)  # Range Not Satisfiable
            elif status_code == 500:
                return JSONResponse(
                    content={"error": "Error reading log file"},
                    status_code=500
                )

            # Return log file content
            headers = {}
            if content_range:
                headers["Content-Range"] = content_range

            return Response(
                content=content,
                media_type="text/plain; charset=UTF-8",
                status_code=status_code,
                headers=headers
            )

        self._add_options_handler("/actuator/logfile")

        # Refresh endpoint - reload configuration from Config Server
        @self.app.post("/actuator/refresh", tags=["actuator"], include_in_schema=False)
        async def refresh():
            """Refresh configuration from Config Server"""
            changed_keys = self.refresh_endpoint.refresh()
            return JSONResponse(content=changed_keys)

        self._add_options_handler("/actuator/refresh")

        # Beans endpoint
        @self.app.get("/actuator/beans", tags=["actuator"], include_in_schema=False)
        async def beans():
            """Get application beans/components"""
            return JSONResponse(content=self.beans_endpoint.get_beans())

        self._add_options_handler("/actuator/beans")

        # ConfigProps endpoint - all configuration properties
        @self.app.get("/actuator/configprops", tags=["actuator"], include_in_schema=False)
        async def configprops_all():
            """Get all configuration properties"""
            return JSONResponse(content=self.configprops_endpoint.get_config_props())

        self._add_options_handler("/actuator/configprops")

        # ConfigProps endpoint - filtered by prefix
        @self.app.get("/actuator/configprops/{prefix}", tags=["actuator"], include_in_schema=False)
        async def configprops_prefix(prefix: str):
            """Get configuration properties by prefix"""
            props = self.configprops_endpoint.get_config_props_by_prefix(prefix)
            if not props.get("contexts", {}).get("application", {}).get("beans"):
                return JSONResponse(content={}, status_code=404)
            return JSONResponse(content=props)

        # ScheduledTasks endpoint
        @self.app.get("/actuator/scheduledtasks", tags=["actuator"], include_in_schema=False)
        async def scheduledtasks():
            """Get scheduled tasks"""
            return JSONResponse(content=self.scheduledtasks_endpoint.get_scheduled_tasks())

        self._add_options_handler("/actuator/scheduledtasks")

        # Heapdump endpoint - returns memory statistics (JSON, not binary)
        @self.app.get("/actuator/heapdump", tags=["actuator"], include_in_schema=False)
        async def heapdump():
            """Get memory statistics"""
            return JSONResponse(content=self.heapdump_endpoint.get_memory_stats())

        self._add_options_handler("/actuator/heapdump")

        # Caches endpoint - all caches
        @self.app.get("/actuator/caches", tags=["actuator"], include_in_schema=False)
        async def caches_all():
            """Get all caches"""
            return JSONResponse(content=self.caches_endpoint.get_caches())

        self._add_options_handler("/actuator/caches")

        # Caches endpoint - single cache
        @self.app.get("/actuator/caches/{cache_name}", tags=["actuator"], include_in_schema=False)
        async def caches_single(cache_name: str, cacheManager: Optional[str] = None):
            """Get single cache"""
            cache = self.caches_endpoint.get_cache(cache_name, cacheManager)
            if cache is None:
                return JSONResponse(
                    content={"error": f"Cache '{cache_name}' not found"},
                    status_code=404
                )
            return JSONResponse(content=cache)

        # Caches endpoint - evict all
        @self.app.delete("/actuator/caches", tags=["actuator"], include_in_schema=False)
        async def caches_evict_all():
            """Evict all caches"""
            self.caches_endpoint.evict_all_caches()
            return Response(status_code=204)

        # Caches endpoint - evict single cache
        @self.app.delete("/actuator/caches/{cache_name}", tags=["actuator"], include_in_schema=False)
        async def caches_evict(cache_name: str, cacheManager: Optional[str] = None):
            """Evict single cache"""
            success = self.caches_endpoint.evict_cache(cache_name, cacheManager)
            if not success:
                return JSONResponse(
                    content={"error": f"Cache '{cache_name}' not found"},
                    status_code=404
                )
            return Response(status_code=204)

        # AuditEvents endpoint
        @self.app.get("/actuator/auditevents", tags=["actuator"], include_in_schema=False)
        async def auditevents(
            principal: Optional[str] = None,
            after: Optional[str] = None,
            type: Optional[str] = None
        ):
            """Get audit events with optional filtering"""
            return JSONResponse(
                content=self.auditevents_endpoint.get_events(
                    principal=principal,
                    after=after,
                    event_type=type
                )
            )

        self._add_options_handler("/actuator/auditevents")

        # OpenAPI v3 endpoint (Spring Boot Admin compatibility)
        @self.app.get("/v3/api-docs", tags=["openapi"])
        async def openapi_v3():
            """OpenAPI v3 specification (Spring Boot Admin compatibility)"""
            return JSONResponse(content=self.app.openapi())

        self._add_options_handler("/v3/api-docs")

        logger.info("Actuator endpoints registered with OPTIONS support: discovery, health, info, prometheus, metrics, env, loggers, mappings, threaddump, httptrace, httpexchanges, dump, trace, logfile, refresh, beans, configprops, scheduledtasks, heapdump, caches, auditevents, v3/api-docs")


def add_actuator_endpoints(
        app: FastAPI,
        base_url: str,
        health_endpoint: Optional[HealthEndpoint] = None,
        info_endpoint: Optional[InfoEndpoint] = None,
        prometheus_endpoint: Optional[PrometheusEndpoint] = None,
        enable_cors: bool = True
) -> FastAPIActuatorIntegration:
    """
    Add Spring Boot Actuator endpoints to FastAPI app.

    Args:
        app: FastAPI application
        base_url: Base URL for the application (e.g., "http://localhost:8080")
        health_endpoint: Custom health endpoint (optional)
        info_endpoint: Custom info endpoint (optional)
        prometheus_endpoint: Custom prometheus endpoint (optional)
        enable_cors: Enable CORS for actuator endpoints (default: True)

    Returns:
        FastAPIActuatorIntegration instance
    """
    return FastAPIActuatorIntegration(
        app=app,
        base_url=base_url,
        health_endpoint=health_endpoint,
        info_endpoint=info_endpoint,
        prometheus_endpoint=prometheus_endpoint,
        enable_cors=enable_cors
    )