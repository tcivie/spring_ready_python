"""Framework integrations (FastAPI, Flask, etc.)"""

from .fastapi import FastAPIActuatorIntegration, add_actuator_endpoints

__all__ = [
    "FastAPIActuatorIntegration",
    "add_actuator_endpoints",
]