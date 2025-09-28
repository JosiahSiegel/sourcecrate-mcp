"""
Enhanced error recovery system with exponential backoff, circuit breakers, and intelligent retry strategies.
Provides comprehensive error handling for various failure scenarios.
"""

import asyncio
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of error types for intelligent retry strategies."""

    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    AUTHENTICATION_ERROR = "auth_error"
    API_ERROR = "api_error"
    PARSE_ERROR = "parse_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_factor: float = 1.0


@dataclass
class ErrorStats:
    """Statistics for error tracking."""

    total_errors: int = 0
    errors_by_type: dict[ErrorType, int] = field(default_factory=dict)
    consecutive_failures: int = 0
    last_error_time: float | None = None
    recovery_attempts: int = 0


class CircuitBreaker:
    """Circuit breaker pattern implementation for error recovery."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "closed"  # closed, open, half_open
        self.half_open_attempts = 0

    def is_available(self) -> bool:
        """Check if the circuit breaker allows operations."""
        if self.state == "closed":
            return True

        if self.state == "open":
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time > self.recovery_timeout
            ):
                self.state = "half_open"
                self.half_open_attempts = 0
                logger.info("🔄 Circuit breaker moving to half-open state")
                return True
            return False

        if self.state == "half_open":
            return self.half_open_attempts < self.half_open_max_calls

        return False

    def record_success(self) -> None:
        """Record a successful operation."""
        if self.state == "half_open":
            self.half_open_attempts += 1
            if self.half_open_attempts >= self.half_open_max_calls:
                self.state = "closed"
                self.failure_count = 0
                logger.info("✅ Circuit breaker closed - service recovered")
        elif self.state == "closed":
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "half_open":
            self.state = "open"
            logger.warning("🚨 Circuit breaker opened - half-open test failed")
        elif self.state == "closed" and self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"🚨 Circuit breaker opened - {self.failure_count} failures")


class EnhancedErrorRecovery:
    """Enhanced error recovery system with intelligent retry strategies."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.circuit_breaker = CircuitBreaker()
        self.error_stats = ErrorStats()
        self.retry_configs: dict[ErrorType, RetryConfig] = {
            ErrorType.NETWORK_ERROR: RetryConfig(max_attempts=5, base_delay=2.0),
            ErrorType.TIMEOUT_ERROR: RetryConfig(max_attempts=3, base_delay=5.0),
            ErrorType.RATE_LIMIT_ERROR: RetryConfig(
                max_attempts=3, base_delay=10.0, max_delay=120.0
            ),
            ErrorType.AUTHENTICATION_ERROR: RetryConfig(
                max_attempts=1
            ),  # Don't retry auth errors
            ErrorType.API_ERROR: RetryConfig(max_attempts=2, base_delay=3.0),
            ErrorType.PARSE_ERROR: RetryConfig(max_attempts=2, base_delay=1.0),
            ErrorType.UNKNOWN_ERROR: RetryConfig(max_attempts=3, base_delay=2.0),
        }

    def classify_error(self, error: Exception) -> ErrorType:
        """Classify error type for intelligent retry strategy."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Network-related errors
        if any(
            keyword in error_str
            for keyword in ["connection", "network", "unreachable", "dns", "socket"]
        ):
            return ErrorType.NETWORK_ERROR

        # Timeout errors
        if any(
            keyword in error_str for keyword in ["timeout", "timed out", "read timeout"]
        ):
            return ErrorType.TIMEOUT_ERROR

        # Rate limiting
        if any(
            keyword in error_str
            for keyword in ["rate limit", "too many requests", "429", "quota exceeded"]
        ):
            return ErrorType.RATE_LIMIT_ERROR

        # Authentication errors
        if any(
            keyword in error_str
            for keyword in ["unauthorized", "401", "403", "authentication", "api key"]
        ):
            return ErrorType.AUTHENTICATION_ERROR

        # API errors
        if any(
            keyword in error_str
            for keyword in ["api error", "bad request", "400", "500", "502", "503"]
        ):
            return ErrorType.API_ERROR

        # Parse errors
        if any(keyword in error_type for keyword in ["json", "parse", "decode", "xml"]):
            return ErrorType.PARSE_ERROR

        return ErrorType.UNKNOWN_ERROR

    def calculate_delay(
        self, attempt: int, error_type: ErrorType, config: RetryConfig | None = None
    ) -> float:
        """Calculate exponential backoff delay with jitter."""
        if config is None:
            config = self.retry_configs[error_type]

        # Base exponential backoff
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))
        delay *= config.backoff_factor

        # Apply jitter to avoid thundering herd
        if config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)

        # Cap at max delay
        delay = min(delay, config.max_delay)

        # Special handling for rate limits - use longer delays
        if error_type == ErrorType.RATE_LIMIT_ERROR:
            delay = max(delay, 5.0 * attempt)

        return delay

    async def execute_with_recovery(
        self,
        operation: Callable[[], Any],
        operation_name: str,
        custom_config: RetryConfig | None = None,
    ) -> Any:
        """
        Execute operation with comprehensive error recovery.

        Args:
            operation: Async function to execute
            operation_name: Name for logging and tracking
            custom_config: Optional custom retry configuration

        Returns:
            Result of successful operation

        Raises:
            Last exception if all retry attempts fail
        """
        if not self.circuit_breaker.is_available():
            raise Exception(f"Circuit breaker is open for {self.service_name}")

        last_exception = None

        for attempt in range(1, 10):  # Max 10 attempts across all error types
            try:
                result = await operation()

                # Record success
                self.circuit_breaker.record_success()
                self.error_stats.consecutive_failures = 0

                if attempt > 1:
                    logger.info(
                        f"✅ {self.service_name}.{operation_name} succeeded on attempt {attempt}"
                    )

                return result

            except Exception as e:
                last_exception = e
                error_type = self.classify_error(e)

                # Update error statistics
                self.error_stats.total_errors += 1
                self.error_stats.errors_by_type[error_type] = (
                    self.error_stats.errors_by_type.get(error_type, 0) + 1
                )
                self.error_stats.consecutive_failures += 1
                self.error_stats.last_error_time = time.time()

                # Get retry configuration
                config = custom_config or self.retry_configs[error_type]

                # Check if we should retry
                if attempt >= config.max_attempts:
                    logger.error(
                        f"❌ {self.service_name}.{operation_name} failed after "
                        f"{attempt} attempts: {e}"
                    )
                    # Record multiple failures for circuit breaker when operation exhausts retries
                    for _ in range(min(attempt, self.circuit_breaker.failure_threshold)):
                        self.circuit_breaker.record_failure()
                    break

                # Calculate delay and wait
                delay = self.calculate_delay(attempt, error_type, config)

                logger.warning(
                    f"⚠️  {self.service_name}.{operation_name} attempt {attempt} failed "
                    f"({error_type.value}): {e}. Retrying in {delay:.1f}s..."
                )

                await asyncio.sleep(delay)

        # All attempts failed
        self.circuit_breaker.record_failure()
        if last_exception:
            raise last_exception
        else:
            raise Exception(f"All retry attempts failed for {operation_name}")

    def get_health_status(self) -> dict[str, Any]:
        """Get current health status and error statistics."""
        return {
            "service_name": self.service_name,
            "circuit_breaker_state": self.circuit_breaker.state,
            "total_errors": self.error_stats.total_errors,
            "consecutive_failures": self.error_stats.consecutive_failures,
            "errors_by_type": {
                error_type.value: count
                for error_type, count in self.error_stats.errors_by_type.items()
            },
            "last_error_time": self.error_stats.last_error_time,
            "recovery_attempts": self.error_stats.recovery_attempts,
            "is_healthy": (
                self.circuit_breaker.state == "closed"
                and self.error_stats.consecutive_failures < 3
            ),
        }

    def reset_error_state(self) -> None:
        """Reset error state for manual recovery."""
        logger.info(f"🔄 Resetting error state for {self.service_name}")
        self.error_stats = ErrorStats()
        self.circuit_breaker = CircuitBreaker()


class GlobalErrorRecoveryManager:
    """Global manager for error recovery across all services."""

    def __init__(self) -> None:
        self.services: dict[str, EnhancedErrorRecovery] = {}

    def get_service_recovery(self, service_name: str) -> EnhancedErrorRecovery:
        """Get or create error recovery instance for a service."""
        if service_name not in self.services:
            self.services[service_name] = EnhancedErrorRecovery(service_name)
        return self.services[service_name]

    def get_global_health_status(self) -> dict[str, Any]:
        """Get health status for all services."""
        return {
            service_name: recovery.get_health_status()
            for service_name, recovery in self.services.items()
        }

    def reset_all_error_states(self) -> None:
        """Reset error states for all services."""
        for recovery in self.services.values():
            recovery.reset_error_state()


# Global instance
global_error_recovery = GlobalErrorRecoveryManager()


# Convenience decorator for adding error recovery to functions
def with_error_recovery(
    service_name: str,
    operation_name: str | None = None,
    custom_config: RetryConfig | None = None,
) -> Any:
    """Decorator to add error recovery to async functions."""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            recovery = global_error_recovery.get_service_recovery(service_name)
            op_name = operation_name or func.__name__

            async def operation() -> Any:
                return await func(*args, **kwargs)

            return await recovery.execute_with_recovery(
                operation, op_name, custom_config
            )

        return wrapper

    return decorator
