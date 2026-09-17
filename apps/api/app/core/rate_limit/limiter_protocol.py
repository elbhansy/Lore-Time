"""Rate Limiter Protocol & Result Data Structures."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int  # Deterministic seconds until capacity is restored (0 if allowed)


@runtime_checkable
class RateLimiter(Protocol):
    def check(self, key: str, limit: int, burst: int) -> RateLimitResult:
        """Evaluates whether the given key is permitted under (limit, burst) rules."""
        ...

    def clear(self) -> None:
        """Clears all tracked state (used primarily in test teardown)."""
        ...
