"""
Eureka instance metadata model.
Represents the JSON structure that Eureka expects.
"""

import socket
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from enum import Enum


class InstanceStatus(Enum):
    """Eureka instance status"""
    UP = "UP"
    DOWN = "DOWN"
    STARTING = "STARTING"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    UNKNOWN = "UNKNOWN"


@dataclass
class DataCenterInfo:
    """Data center information"""
    name: str = "MyOwn"
    _class: str = field(default="com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "@class": self._class,
            "name": self.name
        }


@dataclass
class LeaseInfo:
    """Lease information for Eureka"""
    renewal_interval_in_secs: int = 30
    duration_in_secs: int = 90
    registration_timestamp: int = 0
    last_renewal_timestamp: int = 0
    eviction_timestamp: int = 0
    service_up_timestamp: int = 0


@dataclass
class InstanceInfo:
    """
    Eureka instance information.
    Matches the JSON structure expected by Eureka Server.
    """

    # Required fields
    app: str  # Application name (uppercase)
    instance_id: str  # Unique instance ID
    host_name: str  # Hostname or IP
    ip_addr: str  # IP address
    vip_address: str  # Virtual IP address (usually same as app name lowercase)
    secure_vip_address: str  # Secure VIP address

    # Port configuration
    port: int
    secure_port: int = 443
    port_enabled: bool = True
    secure_port_enabled: bool = False

    # Status
    status: InstanceStatus = InstanceStatus.UP
    overridden_status: InstanceStatus = InstanceStatus.UNKNOWN

    # URLs
    home_page_url: Optional[str] = None
    status_page_url: Optional[str] = None
    health_check_url: Optional[str] = None

    # Lease info
    lease_info: LeaseInfo = field(default_factory=LeaseInfo)

    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)

    # Data center
    data_center_info: DataCenterInfo = field(default_factory=DataCenterInfo)

    # Coordination
    is_coordinating_discovery_server: bool = False
    last_updated_timestamp: int = 0
    last_dirty_timestamp: int = 0
    action_type: str = "ADDED"

    @classmethod
    def create(
            cls,
            app_name: str,
            instance_id: Optional[str] = None,
            host_name: Optional[str] = None,
            ip_addr: Optional[str] = None,
            port: int = 8080,
            secure_port: int = 443,
            metadata: Optional[Dict[str, str]] = None,
            prefer_ip_address: bool = True
    ) -> "InstanceInfo":
        """
        Factory method to create InstanceInfo with sensible defaults.

        Args:
            app_name: Application name
            instance_id: Instance ID (auto-generated if None)
            host_name: Hostname (auto-detected if None)
            ip_addr: IP address (auto-detected if None)
            port: HTTP port
            secure_port: HTTPS port
            metadata: Additional metadata
            prefer_ip_address: Use IP address instead of hostname
        """

        # Auto-detect hostname and IP
        if not host_name:
            host_name = socket.gethostname()

        if not ip_addr:
            try:
                ip_addr = socket.gethostbyname(host_name)
            except socket.gaierror:
                ip_addr = "127.0.0.1"

        # Use IP as hostname if prefer_ip_address is True (like Spring's eureka.instance.prefer-ip-address)
        if prefer_ip_address:
            host_name = ip_addr

        # Generate instance ID if not provided
        if not instance_id:
            instance_id = f"{app_name.lower()}:{host_name}:{port}"

        # Build URLs
        base_url = f"http://{ip_addr}:{port}"

        return cls(
            app=app_name.upper(),
            instance_id=instance_id,
            host_name=host_name,
            ip_addr=ip_addr,
            vip_address=app_name.lower(),
            secure_vip_address=app_name.lower(),
            port=port,
            secure_port=secure_port,
            home_page_url=base_url,
            status_page_url=f"{base_url}/actuator/info",
            health_check_url=f"{base_url}/actuator/health",
            metadata=metadata or {},
            lease_info=LeaseInfo()
        )

    def to_eureka_dict(self) -> Dict[str, Any]:
        """
        Convert to Eureka-compatible dictionary format.

        Returns:
            Dictionary matching Eureka's expected JSON structure
        """
        return {
            "instance": {
                "instanceId": self.instance_id,
                "app": self.app,
                "appGroupName": None,
                "ipAddr": self.ip_addr,
                "sid": "na",
                "homePageUrl": self.home_page_url,
                "statusPageUrl": self.status_page_url,
                "healthCheckUrl": self.health_check_url,
                "secureHealthCheckUrl": None,
                "vipAddress": self.vip_address,
                "secureVipAddress": self.secure_vip_address,
                "countryId": 1,
                "dataCenterInfo": self.data_center_info.to_dict(),
                "hostName": self.host_name,
                "status": self.status.value,
                "overriddenStatus": self.overridden_status.value,
                "leaseInfo": {
                    "renewalIntervalInSecs": self.lease_info.renewal_interval_in_secs,
                    "durationInSecs": self.lease_info.duration_in_secs,
                    "registrationTimestamp": self.lease_info.registration_timestamp,
                    "lastRenewalTimestamp": self.lease_info.last_renewal_timestamp,
                    "evictionTimestamp": self.lease_info.eviction_timestamp,
                    "serviceUpTimestamp": self.lease_info.service_up_timestamp,
                },
                "metadata": self.metadata,
                "port": {
                    "$": self.port,
                    "@enabled": str(self.port_enabled).lower()
                },
                "securePort": {
                    "$": self.secure_port,
                    "@enabled": str(self.secure_port_enabled).lower()
                },
                "isCoordinatingDiscoveryServer": str(self.is_coordinating_discovery_server).lower(),
                "lastUpdatedTimestamp": str(self.last_updated_timestamp),
                "lastDirtyTimestamp": str(self.last_dirty_timestamp),
                "actionType": self.action_type
            }
        }