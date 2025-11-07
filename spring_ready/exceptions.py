"""Custom exceptions for spring-ready library"""


class SpringReadyException(Exception):
    """Base exception for all spring-ready errors"""
    pass


class EurekaRegistrationError(SpringReadyException):
    """Raised when Eureka registration fails"""
    pass


class EurekaHeartbeatError(SpringReadyException):
    """Raised when Eureka heartbeat fails"""
    pass


class ConfigServerError(SpringReadyException):
    """Raised when Config Server is unreachable or returns invalid config"""
    pass


class ServiceDiscoveryError(SpringReadyException):
    """Raised when service discovery fails"""
    pass