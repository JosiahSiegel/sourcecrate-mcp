"""
Unit tests for enhanced error recovery functionality.
Tests circuit breakers, exponential backoff, and intelligent retry strategies.
"""

import time

import pytest

from paperez_mcp.utils.enhanced_error_recovery import (
    CircuitBreaker,
    EnhancedErrorRecovery,
    ErrorType,
    RetryConfig,
    global_error_recovery,
    with_error_recovery,
)


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1.0,  # Short timeout for testing
            half_open_max_calls=2,
        )

    def test_initial_state(self):
        """Test circuit breaker initial state."""
        assert self.circuit_breaker.is_available() is True
        assert self.circuit_breaker.state == "closed"
        assert self.circuit_breaker.failure_count == 0

    def test_successful_operations(self):
        """Test circuit breaker with successful operations."""
        # Record some failures first
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        assert self.circuit_breaker.failure_count == 2

        # Record success should reduce failure count
        self.circuit_breaker.record_success()
        assert self.circuit_breaker.failure_count == 1

    def test_circuit_breaker_opening(self):
        """Test circuit breaker opening on failures."""
        # Record failures up to threshold
        for _ in range(3):
            self.circuit_breaker.record_failure()

        # Circuit should be open now
        assert self.circuit_breaker.state == "open"
        assert self.circuit_breaker.is_available() is False

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        # Open the circuit
        for _ in range(3):
            self.circuit_breaker.record_failure()

        assert self.circuit_breaker.state == "open"

        # Wait for recovery timeout
        time.sleep(1.1)

        # Should transition to half-open
        assert self.circuit_breaker.is_available() is True
        assert self.circuit_breaker.state == "half_open"

    def test_half_open_state(self):
        """Test half-open state behavior."""
        # Force circuit to half-open state
        self.circuit_breaker.state = "half_open"
        self.circuit_breaker.half_open_attempts = 0

        # Should allow limited calls
        assert self.circuit_breaker.is_available() is True
        self.circuit_breaker.half_open_attempts = 1

        assert self.circuit_breaker.is_available() is True
        self.circuit_breaker.half_open_attempts = 2

        # Should not allow more calls beyond max
        assert self.circuit_breaker.is_available() is False

    def test_half_open_success_recovery(self):
        """Test successful recovery from half-open state."""
        # Set to half-open
        self.circuit_breaker.state = "half_open"
        self.circuit_breaker.half_open_attempts = 1

        # Successful operations in half-open
        self.circuit_breaker.record_success()
        self.circuit_breaker.record_success()

        # Should close the circuit
        assert self.circuit_breaker.state == "closed"
        assert self.circuit_breaker.failure_count == 0

    def test_half_open_failure_reopening(self):
        """Test circuit reopening on failure in half-open state."""
        # Set to half-open
        self.circuit_breaker.state = "half_open"

        # Failure in half-open should reopen circuit
        self.circuit_breaker.record_failure()

        assert self.circuit_breaker.state == "open"


class TestEnhancedErrorRecovery:
    """Test suite for EnhancedErrorRecovery class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.recovery = EnhancedErrorRecovery("test_service")

    def test_error_classification(self):
        """Test error type classification."""
        # Test network errors
        network_error = Exception("Connection timeout")
        assert self.recovery.classify_error(network_error) == ErrorType.NETWORK_ERROR

        # Test timeout errors
        timeout_error = Exception("Request timed out")
        assert self.recovery.classify_error(timeout_error) == ErrorType.TIMEOUT_ERROR

        # Test rate limit errors
        rate_limit_error = Exception("Too many requests - 429")
        assert (
            self.recovery.classify_error(rate_limit_error) == ErrorType.RATE_LIMIT_ERROR
        )

        # Test authentication errors
        auth_error = Exception("Unauthorized - 401")
        assert (
            self.recovery.classify_error(auth_error) == ErrorType.AUTHENTICATION_ERROR
        )

        # Test API errors
        api_error = Exception("Bad request - 400")
        assert self.recovery.classify_error(api_error) == ErrorType.API_ERROR

        # Test unknown errors
        unknown_error = Exception("Some random error")
        assert self.recovery.classify_error(unknown_error) == ErrorType.UNKNOWN_ERROR

    def test_delay_calculation(self):
        """Test exponential backoff delay calculation."""
        # Test base delay
        delay = self.recovery.calculate_delay(1, ErrorType.NETWORK_ERROR)
        assert delay >= 1.8  # Base delay with jitter (2.0 * 0.9)
        assert delay <= 2.2  # Base delay with jitter (2.0 * 1.1)

        # Test exponential growth
        delay2 = self.recovery.calculate_delay(2, ErrorType.NETWORK_ERROR)
        assert delay2 > delay

        # Test rate limit special handling
        rate_delay = self.recovery.calculate_delay(2, ErrorType.RATE_LIMIT_ERROR)
        assert rate_delay >= 10.0  # Should be at least 5.0 * 2

        # Test max delay cap
        config = RetryConfig(max_delay=5.0)
        large_delay = self.recovery.calculate_delay(10, ErrorType.NETWORK_ERROR, config)
        assert large_delay <= 5.0

    @pytest.mark.asyncio
    async def test_successful_operation(self):
        """Test successful operation execution."""

        async def successful_operation():
            return "success"

        result = await self.recovery.execute_with_recovery(
            successful_operation, "test_op"
        )

        assert result == "success"
        assert self.recovery.error_stats.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_operation_with_retries(self):
        """Test operation that fails then succeeds."""
        call_count = 0

        async def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Network error")
            return "success"

        result = await self.recovery.execute_with_recovery(
            failing_then_succeeding, "test_op"
        )

        assert result == "success"
        assert call_count == 3
        assert self.recovery.error_stats.total_errors == 2

    @pytest.mark.asyncio
    async def test_operation_max_retries(self):
        """Test operation that exceeds max retries."""

        async def always_failing():
            raise Exception("Network error")

        with pytest.raises(Exception):
            await self.recovery.execute_with_recovery(always_failing, "test_op")

        # Should have tried multiple times
        assert self.recovery.error_stats.total_errors > 1
        assert self.recovery.circuit_breaker.state == "open"

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test circuit breaker integration with recovery."""
        # Force circuit breaker open
        self.recovery.circuit_breaker.state = "open"

        async def some_operation():
            return "success"

        with pytest.raises(Exception, match="Circuit breaker is open"):
            await self.recovery.execute_with_recovery(some_operation, "test_op")

    def test_health_status(self):
        """Test health status reporting."""
        status = self.recovery.get_health_status()

        assert status["service_name"] == "test_service"
        assert status["circuit_breaker_state"] == "closed"
        assert status["total_errors"] == 0
        assert status["is_healthy"] is True

        # Simulate some errors
        self.recovery.error_stats.total_errors = 5
        self.recovery.error_stats.consecutive_failures = 2

        status = self.recovery.get_health_status()
        assert status["total_errors"] == 5
        assert status["consecutive_failures"] == 2

    def test_reset_error_state(self):
        """Test error state reset functionality."""
        # Create some error state
        self.recovery.error_stats.total_errors = 10
        self.recovery.error_stats.consecutive_failures = 5
        self.recovery.circuit_breaker.failure_count = 3

        # Reset state
        self.recovery.reset_error_state()

        # Should be back to initial state
        assert self.recovery.error_stats.total_errors == 0
        assert self.recovery.error_stats.consecutive_failures == 0
        assert self.recovery.circuit_breaker.failure_count == 0


class TestGlobalErrorRecoveryManager:
    """Test suite for GlobalErrorRecoveryManager class."""

    def test_service_recovery_creation(self):
        """Test service recovery instance creation."""
        service1 = global_error_recovery.get_service_recovery("service1")
        service2 = global_error_recovery.get_service_recovery("service2")

        assert service1.service_name == "service1"
        assert service2.service_name == "service2"
        assert service1 is not service2

        # Getting same service should return same instance
        service1_again = global_error_recovery.get_service_recovery("service1")
        assert service1 is service1_again

    def test_global_health_status(self):
        """Test global health status reporting."""
        # Create some services
        global_error_recovery.get_service_recovery("service1")
        global_error_recovery.get_service_recovery("service2")

        status = global_error_recovery.get_global_health_status()

        assert "service1" in status
        assert "service2" in status
        assert status["service1"]["service_name"] == "service1"
        assert status["service2"]["service_name"] == "service2"

    def test_reset_all_error_states(self):
        """Test resetting all service error states."""
        # Create services with errors
        service1 = global_error_recovery.get_service_recovery("service1")
        service2 = global_error_recovery.get_service_recovery("service2")

        service1.error_stats.total_errors = 5
        service2.error_stats.total_errors = 3

        # Reset all
        global_error_recovery.reset_all_error_states()

        assert service1.error_stats.total_errors == 0
        assert service2.error_stats.total_errors == 0


class TestErrorRecoveryDecorator:
    """Test suite for error recovery decorator."""

    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test decorator with successful function."""

        @with_error_recovery("test_service", "test_operation")
        async def successful_function(x, y):
            return x + y

        result = await successful_function(1, 2)
        assert result == 3

    @pytest.mark.asyncio
    async def test_decorator_with_retries(self):
        """Test decorator with function that retries."""
        call_count = 0

        @with_error_recovery("test_service", "test_operation")
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Network error")
            return "success"

        result = await failing_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_custom_config(self):
        """Test decorator with custom retry configuration."""
        call_count = 0
        custom_config = RetryConfig(max_attempts=1, base_delay=0.1)

        @with_error_recovery("test_service", "test_operation", custom_config)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")

        with pytest.raises(Exception):
            await failing_function()

        # Should only try once due to custom config
        assert call_count == 1


class TestRetryConfig:
    """Test suite for RetryConfig class."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.backoff_factor == 1.0

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=60.0,
            exponential_base=3.0,
            jitter=False,
            backoff_factor=1.5,
        )

        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.backoff_factor == 1.5
