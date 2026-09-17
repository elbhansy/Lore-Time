"""Unit tests for centralized safe retry classification and bounded retry policies."""

import pytest
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import (
    IntegrityError,
    InterfaceError,
    InternalError,
    OperationalError,
    ProgrammingError,
    SQLAlchemyError,
)
from sqlalchemy.exc import (
    TimeoutError as SATimeoutError,
)

from apps.api.app.application.exceptions import (
    ApplicationError,
    CharacterNotFound,
    ConflictError,
    DatabaseTimeout,
    DatabaseUnavailable,
    EntityNotFound,
    InfrastructureError,
    InvalidChapter,
    ResourceNotFound,
    SeriesNotFound,
    TransactionFailure,
)
from apps.api.app.application.exceptions import (
    ValidationError as AppValidationError,
)
from apps.api.app.core.retry import (
    RetryClassification,
    RetryPolicy,
    classify_failure,
    is_retryable,
)
from packages.domain.publishing.canonical_publisher import PublicationDomainError

# ==============================================================================
# 1. RETRYABLE FAILURES CLASSIFICATION TESTS
# ==============================================================================


@pytest.mark.parametrize(
    "exc_instance",
    [
        DatabaseUnavailable("PostgreSQL connection pool exhausted"),
        DatabaseTimeout("Statement timeout after 30000ms"),
        TransactionFailure("Serialization failure during commit"),
        OperationalError("connection refused", {}, Exception("TCP down")),
        SATimeoutError("QueuePool limit of size 10 overflow 20 reached"),
        InterfaceError("connection already closed", {}, Exception()),
        ConnectionError("Network interface unreachable"),
        TimeoutError("Socket recv timed out"),
        InfrastructureError("Generic underlying infrastructure failure"),
    ],
)
def test_retryable_failures_classified_correctly(exc_instance):
    """Verifies that transient infrastructure and network failures are classified as RETRYABLE."""
    assert classify_failure(exc_instance) == RetryClassification.RETRYABLE
    assert is_retryable(exc_instance) is True


@pytest.mark.parametrize(
    "exc_class",
    [
        DatabaseUnavailable,
        DatabaseTimeout,
        TransactionFailure,
        OperationalError,
        SATimeoutError,
        InterfaceError,
        ConnectionError,
        TimeoutError,
        InfrastructureError,
    ],
)
def test_retryable_exception_classes_classified_correctly(exc_class):
    """Verifies that exception classes themselves are accurately classified."""
    assert classify_failure(exc_class) == RetryClassification.RETRYABLE
    assert is_retryable(exc_class) is True


# ==============================================================================
# 2. NON-RETRYABLE FAILURES CLASSIFICATION TESTS
# ==============================================================================


def _create_pydantic_validation_error():
    class DummyModel(BaseModel):
        num: int = Field(gt=0)

    try:
        DummyModel(num=-1)
    except PydanticValidationError as e:
        return e


@pytest.mark.parametrize(
    "exc_instance",
    [
        AppValidationError("Reader chapter out of bounds"),
        InvalidChapter("Chapter 500 does not exist in series"),
        RequestValidationError(
            [{"loc": ("query", "chapter"), "msg": "field required"}]
        ),
        _create_pydantic_validation_error(),
        ConflictError("Review item status conflict"),
        IntegrityError(
            "duplicate key value violates unique constraint", {}, Exception()
        ),
        ResourceNotFound("Series 123 not found"),
        SeriesNotFound("Series not found"),
        CharacterNotFound("Character not found"),
        EntityNotFound("Entity not found"),
        PublicationDomainError("Cannot publish fact without resolved subject_id"),
        ValueError("Invalid format"),
        TypeError("Unsupported operand"),
        KeyError("missing_key"),
        ProgrammingError("relation does not exist", {}, Exception()),
        InternalError("PostgreSQL syntax error", {}, Exception()),
        SQLAlchemyError("Generic unhandled SQL error"),
        ApplicationError("Generic application error"),
        Exception("Generic unknown error"),
    ],
)
def test_non_retryable_failures_classified_correctly(exc_instance):
    """Verifies that validation, business rule violations, conflicts, and permanent domain errors are NEVER retried."""
    assert classify_failure(exc_instance) == RetryClassification.NON_RETRYABLE
    assert is_retryable(exc_instance) is False


@pytest.mark.parametrize(
    "exc_class",
    [
        AppValidationError,
        InvalidChapter,
        RequestValidationError,
        PydanticValidationError,
        ConflictError,
        IntegrityError,
        ResourceNotFound,
        SeriesNotFound,
        CharacterNotFound,
        EntityNotFound,
        PublicationDomainError,
        ValueError,
        TypeError,
        KeyError,
        ProgrammingError,
        InternalError,
        SQLAlchemyError,
        ApplicationError,
        Exception,
    ],
)
def test_non_retryable_exception_classes_classified_correctly(exc_class):
    """Verifies that exception classes for permanent domain/validation errors are classified as NON_RETRYABLE."""
    assert classify_failure(exc_class) == RetryClassification.NON_RETRYABLE
    assert is_retryable(exc_class) is False


# ==============================================================================
# 3. BOUNDED RETRY POLICY & NO INFINITE RETRIES TESTS
# ==============================================================================


def test_retry_policy_validation_guards():
    """Verifies bounds on retry policies preventing infinite or invalid retries."""
    # Negative retries forbidden
    with pytest.raises(ValueError, match="max_retries cannot be negative"):
        RetryPolicy(max_retries=-1)

    # Exceeding safe ceiling forbidden (guards against runaway loops)
    with pytest.raises(ValueError, match="max_retries exceeds safe bounded limit"):
        RetryPolicy(max_retries=100)

    # Invalid delay timings forbidden
    with pytest.raises(ValueError, match="initial_delay_seconds cannot be negative"):
        RetryPolicy(initial_delay_seconds=-0.1)

    with pytest.raises(
        ValueError, match="max_delay_seconds cannot be less than initial_delay_seconds"
    ):
        RetryPolicy(initial_delay_seconds=2.0, max_delay_seconds=1.0)


def test_retry_policy_immediate_failure_on_non_retryable():
    """Policy must abort immediately without retry when encountering NON_RETRYABLE errors."""
    policy = RetryPolicy(max_retries=3, initial_delay_seconds=0.001, jitter=False)
    call_count = 0

    def failing_func():
        nonlocal call_count
        call_count += 1
        raise AppValidationError("Permanent schema validation error")

    with pytest.raises(AppValidationError, match="Permanent schema validation error"):
        policy.execute(failing_func)

    assert call_count == 1, "Validation error must NOT be retried!"


def test_retry_policy_recovers_after_transient_retryable_failure():
    """Policy retries on RETRYABLE failure and returns value upon recovery."""
    policy = RetryPolicy(max_retries=3, initial_delay_seconds=0.001, jitter=False)
    call_count = 0

    def transient_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise DatabaseUnavailable("DB down temporarily")
        return "success"

    result = policy.execute(transient_func)
    assert result == "success"
    assert call_count == 3, "Should succeed on 3rd attempt after 2 transient failures"


def test_retry_policy_exhausts_retries_and_raises_without_infinite_loop():
    """Policy must strictly respect max_retries limit and terminate cleanly."""
    policy = RetryPolicy(max_retries=3, initial_delay_seconds=0.001, jitter=False)
    call_count = 0

    def always_failing_func():
        nonlocal call_count
        call_count += 1
        raise DatabaseTimeout("DB timed out repeatedly")

    with pytest.raises(DatabaseTimeout, match="DB timed out repeatedly"):
        policy.execute(always_failing_func)

    # Initial attempt (1) + 3 retries = 4 total invocations
    assert call_count == 4, "Must not execute more than initial attempt + max_retries"


def test_retry_policy_computes_exponential_backoff_and_jitter():
    """Verifies exponential delay progression and max cap."""
    policy = RetryPolicy(
        max_retries=5,
        initial_delay_seconds=0.1,
        max_delay_seconds=0.5,
        backoff_factor=2.0,
        jitter=False,
    )

    # Attempt 1: 0.1 * 2^0 = 0.1
    assert pytest.approx(policy.compute_delay(1)) == 0.1
    # Attempt 2: 0.1 * 2^1 = 0.2
    assert pytest.approx(policy.compute_delay(2)) == 0.2
    # Attempt 3: 0.1 * 2^2 = 0.4
    assert pytest.approx(policy.compute_delay(3)) == 0.4
    # Attempt 4: 0.1 * 2^3 = 0.8 -> capped at 0.5
    assert pytest.approx(policy.compute_delay(4)) == 0.5
    # Attempt 5: capped at 0.5
    assert pytest.approx(policy.compute_delay(5)) == 0.5

    # Jitter enabled stays within [0, capped_delay]
    jitter_policy = RetryPolicy(
        max_retries=3,
        initial_delay_seconds=0.1,
        max_delay_seconds=0.5,
        backoff_factor=2.0,
        jitter=True,
    )
    for attempt in range(1, 4):
        delay = jitter_policy.compute_delay(attempt)
        assert 0.0 <= delay <= 0.5
