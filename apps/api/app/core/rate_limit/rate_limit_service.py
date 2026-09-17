"""High-level Rate Limiter Service with throttled error logging and fail-safe degradation."""

import logging
import time
from typing import Any

from apps.api.app.config import Settings, get_settings

from .limiter_protocol import RateLimiter, RateLimitResult
from .sliding_window_counter import SlidingWindowRateLimiter
from .tier_classifier import EndpointTier

logger = logging.getLogger("timeline.rate_limit")


class RateLimitService:
    """Orchestrates rate limit checks across tiers, bounds, and throttled failure logging."""

    def __init__(
        self, limiter: RateLimiter | None = None, settings: Settings | None = None
    ):
        self._settings = settings or get_settings()
        self._limiter: RateLimiter = limiter or SlidingWindowRateLimiter(
            max_identities=self._settings.RATE_LIMIT_MAX_IDENTITIES,
            max_hits_per_identity=self._settings.RATE_LIMIT_MAX_HITS_PER_IDENTITY,
            window_seconds=self._settings.RATE_LIMIT_WINDOW_SECONDS,
        )
        self._last_error_log_time: float = 0.0

    @property
    def is_enabled(self) -> bool:
        # Multi-worker safety enforcement: in-process limiter disabled if worker_count > 1
        if self._settings.WORKER_COUNT > 1:
            return False
        return self._settings.RATE_LIMIT_ENABLED

    def check_rate_limit(self, key: str, tier: EndpointTier) -> RateLimitResult:
        """Evaluates rate limit for key and tier. Fails open on unexpected error with throttled logging."""
        if not self.is_enabled or tier == EndpointTier.EXEMPT:
            return RateLimitResult(allowed=True, limit=0, remaining=0, retry_after=0)

        # Map tier to limits
        if tier == EndpointTier.EXPENSIVE_READ:
            limit = self._settings.RATE_LIMIT_EXPENSIVE_LIMIT
            burst = self._settings.RATE_LIMIT_EXPENSIVE_BURST
        elif tier == EndpointTier.MUTATING:
            limit = self._settings.RATE_LIMIT_MUTATING_LIMIT
            burst = self._settings.RATE_LIMIT_MUTATING_BURST
        else:
            limit = self._settings.RATE_LIMIT_DEFAULT_LIMIT
            burst = self._settings.RATE_LIMIT_DEFAULT_BURST

        try:
            return self._limiter.check(key=key, limit=limit, burst=burst)
        except Exception as e:
            # Fail-open with throttled logging to prevent log storms
            now = time.time()
            if now - self._last_error_log_time >= 5.0:
                self._last_error_log_time = now
                logger.critical(
                    "Rate limiter internal exception: %s. Failing open to preserve availability.",
                    e,
                    extra={
                        "event": "rate_limit.error",
                        "error": str(e),
                        "outcome": "fail_open",
                    },
                )
            return RateLimitResult(
                allowed=True, limit=limit, remaining=1, retry_after=0
            )

    def clear(self) -> None:
        self._limiter.clear()

    def stats(self) -> dict[str, Any]:
        if hasattr(self._limiter, "stats"):
            return self._limiter.stats()
        return {}


_default_rate_limit_service: RateLimitService | None = None


def get_rate_limit_service() -> RateLimitService:
    global _default_rate_limit_service
    if _default_rate_limit_service is None:
        _default_rate_limit_service = RateLimitService()
    return _default_rate_limit_service


def reset_rate_limit_service_for_testing(
    new_service: RateLimitService | None = None,
) -> RateLimitService | None:
    global _default_rate_limit_service
    _default_rate_limit_service = new_service
    return _default_rate_limit_service
