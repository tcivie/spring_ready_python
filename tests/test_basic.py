"""
Basic tests for spring-ready-python

Run with: pytest tests/
"""

import pytest
from spring_ready.eureka.instance import InstanceInfo, InstanceStatus
from spring_ready.retry import RetryConfig, retry_with_backoff
from spring_ready.actuator.health import HealthEndpoint, HealthStatus
from spring_ready.actuator.info import InfoEndpoint


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