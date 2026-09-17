"""Centralized Safe Retry Classification and Policy Engine.

Distinguishes transient/retryable system failures from permanent non-retryable failures.
Enforces non-infinite, jittered exponential backoff retry execution for RETRYABLE errors.
"""

import inspect
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeVar

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import (
    IntegrityError,
    InterfaceError,
    OperationalError,
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
from packages.domain.publishing.canonical_publisher import PublicationDomainError

logger = logging.getLogger("timeline.retry")

T = TypeVar("T")


class RetryClassification(StrEnum):
    RETRYABLE = "RETRYABLE"
    NON_RETRYABLE = "NON_RETRYABLE"


# Explicitly defined retryable exception types
RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    DatabaseUnavailable,
    DatabaseTimeout,
    TransactionFailure,
    OperationalError,
    SATimeoutError,
    InterfaceError,
    ConnectionError,
    TimeoutError,
)

# Explicitly defined non-retryable exception types
NON_RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    AppValidationError,
    RequestValidationError,
    PydanticValidationError,
    InvalidChapter,
    ConflictError,
    IntegrityError,
    ResourceNotFound,
    SeriesNotFound,
    CharacterNotFound,
    EntityNotFound,
    PublicationDomainError,
    KeyError,
    ValueError,
    TypeError,
)


def classify_failure(exc: Exception | type[Exception]) -> RetryClassification:
    """Classifies an exception instance or class into RETRYABLE or NON_RETRYABLE.

    Rules:
    - Transient infrastructure/network/concurrency/timeout errors: RETRYABLE
    - Validation, domain invariants, entity/resource missing, integrity/conflict: NON_RETRYABLE
    - Never retries permanent domain failures or validation errors.
    """
    exc_cls = (
        exc if inspect.isclass(exc) and issubclass(exc, BaseException) else type(exc)
    )

    # 1. Check explicitly non-retryable hierarchies first (safety-first)
    if issubclass(exc_cls, NON_RETRYABLE_EXCEPTIONS):
        return RetryClassification.NON_RETRYABLE

    # 2. Check explicitly retryable hierarchies
    if issubclass(exc_cls, RETRYABLE_EXCEPTIONS):
        return RetryClassification.RETRYABLE

    # 3. Handle general SQLAlchemyError:
    # If not already matched as Operational/Timeout/Interface/Integrity:
    # We treat unknown SQL errors as NON_RETRYABLE by default to avoid retrying SQL syntax/schema bugs.
    if issubclass(exc_cls, SQLAlchemyError):
        return RetryClassification.NON_RETRYABLE

    # 4. Handle general ApplicationError:
    # If it's an InfrastructureError, it's retryable; otherwise domain errors are non-retryable
    if issubclass(exc_cls, InfrastructureError):
        return RetryClassification.RETRYABLE
    if issubclass(exc_cls, ApplicationError):
        return RetryClassification.NON_RETRYABLE

    # 5. Default safe fallback for unknown exceptions: NON_RETRYABLE
    return RetryClassification.NON_RETRYABLE


def is_retryable(exc: Exception | type[Exception]) -> bool:
    """Convenience boolean helper returning True iff failure is RETRYABLE."""
    return classify_failure(exc) == RetryClassification.RETRYABLE


@dataclass(frozen=True)
class RetryPolicy:
    """Configurable bounded retry policy preventing infinite retries."""

    max_retries: int = 3
    initial_delay_seconds: float = 0.05
    max_delay_seconds: float = 2.0
    backoff_factor: float = 2.0
    jitter: bool = True

    def __post_init__(self):
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.max_retries > 10:
            raise ValueError("max_retries exceeds safe bounded limit of 10")
        if self.initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds cannot be negative")
        if self.max_delay_seconds < self.initial_delay_seconds:
            raise ValueError(
                "max_delay_seconds cannot be less than initial_delay_seconds"
            )

    def compute_delay(self, attempt: int) -> float:
        """Computes backoff delay with optional jitter for attempt index (1-based)."""
        raw_delay = self.initial_delay_seconds * (self.backoff_factor ** (attempt - 1))
        capped_delay = min(raw_delay, self.max_delay_seconds)
        if self.jitter:
            return random.uniform(0, capped_delay)
        return capped_delay

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Executes func with safe bounded retry handling.

        Raises immediately on NON_RETRYABLE errors or when max_retries is exhausted.
        """
        attempt = 0
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                classification = classify_failure(exc)
                if classification == RetryClassification.NON_RETRYABLE:
                    logger.warning(
                        "Operation failed with NON_RETRYABLE error %s: %s (no retry)",
                        type(exc).__name__,
                        exc,
                    )
                    raise

                attempt += 1
                if attempt > self.max_retries:
                    logger.error(
                        "Operation exhausted all %d retries for %s: %s",
                        self.max_retries,
                        type(exc).__name__,
                        exc,
                    )
                    raise

                delay = self.compute_delay(attempt)
                logger.info(
                    "Retrying operation (attempt %d/%d) after %.3fs due to %s: %s",
                    attempt,
                    self.max_retries,
                    delay,
                    type(exc).__name__,
                    exc,
                )
                if delay > 0:
                    time.sleep(delay)
