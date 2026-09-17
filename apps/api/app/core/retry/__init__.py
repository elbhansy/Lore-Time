"""Safe Retry and Failure Classification exports."""

from .classifier import (
    NON_RETRYABLE_EXCEPTIONS,
    RETRYABLE_EXCEPTIONS,
    RetryClassification,
    RetryPolicy,
    classify_failure,
    is_retryable,
)

__all__ = [
    "RetryClassification",
    "RETRYABLE_EXCEPTIONS",
    "NON_RETRYABLE_EXCEPTIONS",
    "classify_failure",
    "is_retryable",
    "RetryPolicy",
]
