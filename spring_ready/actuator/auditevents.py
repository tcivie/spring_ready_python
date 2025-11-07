"""
Actuator AuditEvents Endpoint.
Provides information about security-related audit events.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import deque


@dataclass
class AuditEvent:
    """Single audit event"""
    timestamp: str
    principal: str
    type: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "principal": self.principal,
            "type": self.type,
            "data": self.data
        }


class AuditEventsEndpoint:
    """
    AuditEvents endpoint for Spring Boot Actuator compatibility.

    Tracks security-related events like authentication, authorization, etc.
    Stores events in memory with configurable max size.
    """

    def __init__(self, max_events: int = 1000):
        """
        Args:
            max_events: Maximum number of events to keep in memory
        """
        self.max_events = max_events
        self.events: deque = deque(maxlen=max_events)

    def add_event(
        self,
        principal: str,
        event_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an audit event.

        Args:
            principal: Principal (user/system) that triggered the event
            event_type: Event type (e.g., "AUTHENTICATION_SUCCESS", "AUTHORIZATION_FAILURE")
            data: Additional event data
        """
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

        event = AuditEvent(
            timestamp=timestamp,
            principal=principal,
            type=event_type,
            data=data or {}
        )

        self.events.append(event)

    def get_events(
        self,
        principal: Optional[str] = None,
        after: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get audit events with optional filtering.

        Args:
            principal: Filter by principal name
            after: Filter events after this timestamp
            event_type: Filter by event type

        Returns:
            Dictionary with filtered audit events
        """
        filtered_events = list(self.events)

        # Apply filters
        if principal:
            filtered_events = [e for e in filtered_events if e.principal == principal]

        if after:
            filtered_events = [e for e in filtered_events if e.timestamp > after]

        if event_type:
            filtered_events = [e for e in filtered_events if e.type == event_type]

        return {
            "events": [event.to_dict() for event in filtered_events]
        }


def create_default_auditevents_endpoint(max_events: int = 1000) -> AuditEventsEndpoint:
    """
    Create auditevents endpoint with default configuration.

    Args:
        max_events: Maximum number of events to keep

    Returns:
        AuditEventsEndpoint instance
    """
    return AuditEventsEndpoint(max_events=max_events)
