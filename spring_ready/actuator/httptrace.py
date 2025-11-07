"""
Actuator HTTP Trace Endpoint.
Records and displays recent HTTP request-response exchanges.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import deque


@dataclass
class HttpExchange:
    """Single HTTP request-response exchange"""
    timestamp: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    timeTaken: int  # milliseconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "request": self.request,
            "response": self.response,
            "timeTaken": self.timeTaken
        }


class HttpTraceEndpoint:
    """
    HTTP Trace endpoint for Spring Boot Actuator compatibility.

    Records recent HTTP exchanges (request/response pairs).
    Note: In Spring Boot 2.2+, this was renamed to 'httpexchanges' but
    'httptrace' is still commonly used in Spring Boot Admin.
    """

    def __init__(self, max_traces: int = 100):
        """
        Args:
            max_traces: Maximum number of traces to keep (default: 100)
        """
        self.max_traces = max_traces
        self.traces: deque = deque(maxlen=max_traces)

    def add_trace(
        self,
        method: str,
        uri: str,
        status: int,
        time_taken_ms: int,
        headers: Optional[Dict[str, str]] = None,
        remote_address: Optional[str] = None
    ) -> None:
        """
        Add an HTTP trace.

        Args:
            method: HTTP method (GET, POST, etc.)
            uri: Request URI
            status: Response status code
            time_taken_ms: Time taken in milliseconds
            headers: Request headers (optional)
            remote_address: Remote IP address (optional)
        """
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

        exchange = HttpExchange(
            timestamp=timestamp,
            request={
                "method": method,
                "uri": uri,
                "headers": headers or {},
                "remoteAddress": remote_address
            },
            response={
                "status": status,
                "headers": {}
            },
            timeTaken=time_taken_ms
        )

        self.traces.append(exchange)

    def get_traces(self) -> Dict[str, Any]:
        """
        Get all HTTP traces.

        Returns:
            Dictionary with traces list
        """
        return {
            "traces": [trace.to_dict() for trace in self.traces]
        }


class HttpExchangesEndpoint(HttpTraceEndpoint):
    """
    HTTP Exchanges endpoint (newer name for httptrace in Spring Boot 2.2+).
    Alias for HttpTraceEndpoint with different response format.
    """

    def get_exchanges(self) -> Dict[str, Any]:
        """
        Get all HTTP exchanges (newer format).

        Returns:
            Dictionary with exchanges list
        """
        return {
            "exchanges": [trace.to_dict() for trace in self.traces]
        }


def create_default_httptrace_endpoint(max_traces: int = 100) -> HttpTraceEndpoint:
    """
    Create HTTP trace endpoint with default configuration.

    Args:
        max_traces: Maximum number of traces to keep

    Returns:
        HttpTraceEndpoint instance
    """
    return HttpTraceEndpoint(max_traces=max_traces)


def create_default_httpexchanges_endpoint(max_traces: int = 100) -> HttpExchangesEndpoint:
    """
    Create HTTP exchanges endpoint with default configuration.

    Args:
        max_traces: Maximum number of exchanges to keep

    Returns:
        HttpExchangesEndpoint instance
    """
    return HttpExchangesEndpoint(max_traces=max_traces)
