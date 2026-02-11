"""
Basic tests for spring-ready-python

Run with: pytest tests/
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import threading

from spring_ready.eureka.instance import InstanceInfo, InstanceStatus
from spring_ready.eureka.client import EurekaClient
from spring_ready.eureka.registry import EurekaRegistry
from spring_ready.retry import RetryConfig, retry_with_backoff
from spring_ready.actuator.health import HealthEndpoint, HealthStatus
from spring_ready.actuator.info import InfoEndpoint
from spring_ready.exceptions import (
    EurekaHeartbeatError,
    EurekaInstanceNotFoundError,
    EurekaRegistrationError,
)


class TestInstanceInfo:
    """Test Eureka instance metadata"""

    def test_create_instance_info(self):
        instance = InstanceInfo.create(
            app_name="test-app",
            port=8080
        )

        assert instance.app == "TEST-APP"
        assert instance.port == 8080
        assert instance.status == InstanceStatus.UP
        assert "test-app" in instance.instance_id.lower()

    def test_instance_to_eureka_dict(self):
        instance = InstanceInfo.create(
            app_name="test-app",
            port=8080
        )

        eureka_dict = instance.to_eureka_dict()

        assert "instance" in eureka_dict
        assert eureka_dict["instance"]["app"] == "TEST-APP"
        assert eureka_dict["instance"]["port"]["$"] == 8080


class TestRetry:
    """Test retry logic"""

    def test_retry_success_first_attempt(self):
        call_count = [0]

        def succeed_immediately():
            call_count[0] += 1
            return "success"

        config = RetryConfig(max_attempts=3)
        result = retry_with_backoff(succeed_immediately, config, "test", fail_fast=True)

        assert result == "success"
        assert call_count[0] == 1

    def test_retry_success_after_failures(self):
        call_count = [0]

        def succeed_on_third():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Not yet")
            return "success"

        config = RetryConfig(max_attempts=5, initial_interval=0.01, max_interval=0.02)
        result = retry_with_backoff(succeed_on_third, config, "test", fail_fast=True)

        assert result == "success"
        assert call_count[0] == 3

    def test_retry_all_failures_with_fail_fast(self):
        def always_fail():
            raise ValueError("Always fails")

        config = RetryConfig(max_attempts=3, initial_interval=0.01)

        with pytest.raises(ValueError):
            retry_with_backoff(always_fail, config, "test", fail_fast=True)

    def test_retry_all_failures_without_fail_fast(self):
        def always_fail():
            raise ValueError("Always fails")

        config = RetryConfig(max_attempts=3, initial_interval=0.01)
        result = retry_with_backoff(always_fail, config, "test", fail_fast=False)

        assert result is None


class TestHealthEndpoint:
    """Test health endpoint"""

    def test_health_check_all_up(self):
        health = HealthEndpoint()
        health.add_check("test1", lambda: True)
        health.add_check("test2", lambda: True)

        result = health.check()

        assert result["status"] == HealthStatus.UP.value
        assert "test1" in result["components"]
        assert "test2" in result["components"]
        assert result["components"]["test1"]["status"] == HealthStatus.UP.value

    def test_health_check_one_down(self):
        health = HealthEndpoint()
        health.add_check("test1", lambda: True)
        health.add_check("test2", lambda: False)

        result = health.check()

        assert result["status"] == HealthStatus.DOWN.value
        assert result["components"]["test2"]["status"] == HealthStatus.DOWN.value

    def test_health_check_exception(self):
        health = HealthEndpoint()

        def failing_check():
            raise Exception("Check failed")

        health.add_check("failing", failing_check)

        result = health.check()

        assert result["status"] == HealthStatus.DOWN.value
        assert "failing" in result["components"]
        assert result["components"]["failing"]["status"] == HealthStatus.DOWN.value


class TestInfoEndpoint:
    """Test info endpoint"""

    def test_info_basic(self):
        info = InfoEndpoint(
            app_name="test-app",
            app_version="1.0.0",
            app_description="Test application"
        )

        result = info.get_info()

        assert result["app"]["name"] == "test-app"
        assert result["app"]["version"] == "1.0.0"
        assert result["app"]["description"] == "Test application"
        assert "python" in result

    def test_info_custom_fields(self):
        info = InfoEndpoint(app_name="test-app")
        info.add_info("custom", {"key": "value"})

        result = info.get_info()

        assert "custom" in result
        assert result["custom"]["key"] == "value"


class TestEurekaInstanceNotFoundError:
    """Test the EurekaInstanceNotFoundError exception hierarchy"""

    def test_is_subclass_of_heartbeat_error(self):
        assert issubclass(EurekaInstanceNotFoundError, EurekaHeartbeatError)

    def test_caught_by_heartbeat_error_handler(self):
        with pytest.raises(EurekaHeartbeatError):
            raise EurekaInstanceNotFoundError("instance gone")

    def test_distinguishable_from_heartbeat_error(self):
        err = EurekaInstanceNotFoundError("instance gone")
        assert isinstance(err, EurekaInstanceNotFoundError)
        assert isinstance(err, EurekaHeartbeatError)


class TestEurekaClient404Detection:
    """Test that _request detects 404 and send_heartbeat propagates it"""

    def _make_client(self):
        return EurekaClient(eureka_servers=["http://localhost:8761/eureka/"])

    @patch("spring_ready.eureka.client.requests.request")
    def test_request_raises_instance_not_found_on_404(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        client = self._make_client()

        with pytest.raises(EurekaInstanceNotFoundError):
            client._request("PUT", "/apps/MY-APP/my-instance")

    @patch("spring_ready.eureka.client.requests.request")
    def test_request_does_not_failover_on_404(self, mock_request):
        """404 should raise immediately, not try next server"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        client = EurekaClient(
            eureka_servers=[
                "http://eureka1:8761/eureka/",
                "http://eureka2:8761/eureka/",
            ]
        )

        with pytest.raises(EurekaInstanceNotFoundError):
            client._request("PUT", "/apps/MY-APP/my-instance")

        # Only one request made — no failover
        assert mock_request.call_count == 1

    @patch("spring_ready.eureka.client.requests.request")
    def test_send_heartbeat_propagates_instance_not_found(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        client = self._make_client()

        with pytest.raises(EurekaInstanceNotFoundError):
            client.send_heartbeat("MY-APP", "my-instance")

    @patch("spring_ready.eureka.client.requests.request")
    def test_send_heartbeat_wraps_other_errors(self, mock_request):
        """Non-404 errors should still be wrapped in EurekaHeartbeatError"""
        mock_request.side_effect = ConnectionError("connection refused")

        client = self._make_client()

        with pytest.raises(EurekaHeartbeatError):
            client.send_heartbeat("MY-APP", "my-instance")


class TestEurekaRegistryReconnection:
    """Test reconnection logic in EurekaRegistry"""

    def _make_instance(self):
        return InstanceInfo.create(app_name="test-app", port=8080)

    def _make_registry(self, instance=None):
        registry = EurekaRegistry(
            eureka_servers=["http://localhost:8761/eureka/"],
            instance_info=instance or self._make_instance(),
            retry_config=RetryConfig(max_attempts=1, initial_interval=0.01),
            fail_fast=False,
        )
        return registry

    def test_attempt_reregistration_success(self):
        registry = self._make_registry()
        registry.client.register = MagicMock()

        result = registry._attempt_reregistration()

        assert result is True
        assert registry._registered is True
        registry.client.register.assert_called_once_with(registry.instance)

    def test_attempt_reregistration_failure(self):
        registry = self._make_registry()
        registry.client.register = MagicMock(side_effect=EurekaRegistrationError("down"))

        result = registry._attempt_reregistration()

        assert result is False
        assert registry._registered is False

    @patch("spring_ready.eureka.client.requests.request")
    def test_start_always_starts_heartbeat_thread(self, mock_request):
        """Heartbeat thread should start even if initial registration fails"""
        mock_request.side_effect = ConnectionError("Eureka down")

        registry = self._make_registry()
        registry.instance.lease_info.renewal_interval_in_secs = 0.01
        registry.start()

        assert registry._registered is False
        assert registry._heartbeat_thread is not None
        assert registry._heartbeat_thread.is_alive()

        # Clean up
        registry.shutdown()

    def test_shutdown_stops_thread_when_unregistered(self):
        """shutdown() should stop heartbeat thread even when not registered"""
        registry = self._make_registry()
        registry._registered = False
        registry.instance.lease_info.renewal_interval_in_secs = 0.01

        # Mock register to keep failing (so loop stays in retry mode)
        registry.client.register = MagicMock(side_effect=EurekaRegistrationError("down"))
        registry.client.deregister = MagicMock()

        # Manually start a heartbeat thread
        registry._stop_heartbeat.clear()
        registry._heartbeat_thread = threading.Thread(
            target=registry._heartbeat_loop,
            daemon=True,
        )
        registry._heartbeat_thread.start()

        registry.shutdown()

        assert not registry._heartbeat_thread.is_alive()
        registry.client.deregister.assert_not_called()

    def test_heartbeat_loop_retries_registration_when_unregistered(self):
        """When not registered, heartbeat loop should attempt registration"""
        registry = self._make_registry()
        registry._registered = False
        registry.instance.lease_info.renewal_interval_in_secs = 0.01

        attempt_count = [0]

        def mock_register(instance):
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise EurekaRegistrationError("still down")
            # Second attempt succeeds — stop the loop after

        def mock_heartbeat(app_name, instance_id):
            # Once registered, first heartbeat stops the loop
            registry._stop_heartbeat.set()

        registry.client.register = mock_register
        registry.client.send_heartbeat = mock_heartbeat

        registry._heartbeat_loop()

        assert attempt_count[0] == 2
        assert registry._registered is True

    def test_heartbeat_loop_reregisters_on_404(self):
        """On EurekaInstanceNotFoundError, loop should re-register"""
        registry = self._make_registry()
        registry._registered = True
        registry.instance.lease_info.renewal_interval_in_secs = 0.01

        heartbeat_calls = [0]

        def mock_heartbeat(app_name, instance_id):
            heartbeat_calls[0] += 1
            if heartbeat_calls[0] == 1:
                raise EurekaInstanceNotFoundError("evicted")
            # Second call succeeds — stop the loop
            registry._stop_heartbeat.set()

        registry.client.send_heartbeat = mock_heartbeat
        registry.client.register = MagicMock()  # Re-registration succeeds

        registry._heartbeat_loop()

        assert heartbeat_calls[0] == 2
        registry.client.register.assert_called_once()
        assert registry._registered is True