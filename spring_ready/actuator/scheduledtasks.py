"""
Actuator ScheduledTasks Endpoint.
Shows information about scheduled tasks.
"""

from typing import Dict, Any, List


class ScheduledTasksEndpoint:
    """
    ScheduledTasks endpoint for Spring Boot Actuator compatibility.

    Shows information about scheduled tasks.
    In Python context, this would integrate with APScheduler, Celery Beat, or asyncio tasks.
    For now, returns empty structure indicating no scheduled tasks configured.
    """

    def __init__(self):
        """Initialize scheduled tasks endpoint"""
        self.cron_tasks: List[Dict[str, Any]] = []
        self.fixed_delay_tasks: List[Dict[str, Any]] = []
        self.fixed_rate_tasks: List[Dict[str, Any]] = []

    def get_scheduled_tasks(self) -> Dict[str, Any]:
        """
        Get all scheduled tasks.

        Returns:
            Dictionary with cron, fixedDelay, and fixedRate tasks
        """
        return {
            "cron": self.cron_tasks,
            "fixedDelay": self.fixed_delay_tasks,
            "fixedRate": self.fixed_rate_tasks
        }

    def add_cron_task(self, name: str, expression: str, runnable: str) -> None:
        """
        Add a cron task.

        Args:
            name: Task name
            expression: Cron expression
            runnable: Runnable target
        """
        self.cron_tasks.append({
            "runnable": {
                "target": runnable
            },
            "expression": expression
        })

    def add_fixed_delay_task(self, name: str, interval: int, runnable: str) -> None:
        """
        Add a fixed delay task.

        Args:
            name: Task name
            interval: Delay interval in milliseconds
            runnable: Runnable target
        """
        self.fixed_delay_tasks.append({
            "runnable": {
                "target": runnable
            },
            "initialDelay": 0,
            "interval": interval
        })

    def add_fixed_rate_task(self, name: str, interval: int, runnable: str) -> None:
        """
        Add a fixed rate task.

        Args:
            name: Task name
            interval: Rate interval in milliseconds
            runnable: Runnable target
        """
        self.fixed_rate_tasks.append({
            "runnable": {
                "target": runnable
            },
            "initialDelay": 0,
            "interval": interval
        })


def create_default_scheduledtasks_endpoint() -> ScheduledTasksEndpoint:
    """
    Create scheduledtasks endpoint with default configuration.

    Returns:
        ScheduledTasksEndpoint instance
    """
    return ScheduledTasksEndpoint()
