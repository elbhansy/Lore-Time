"""High-level Cache Orchestrator and Service."""

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

from apps.api.app.config import Settings, get_settings

from .cache_backend import CacheBackend
from .key_builder import build_cache_key, build_series_prefix
from .memory_cache import BoundedMemoryCache

logger = logging.getLogger("timeline.cache")
T = TypeVar("T")


class CacheService:
    """Orchestrates caching operations with transparent failure degradation,
    dirty namespace tracking, and structured logging."""

    def __init__(
        self, backend: CacheBackend | None = None, settings: Settings | None = None
    ):
        self._settings = settings or get_settings()
        self._backend: CacheBackend = backend or BoundedMemoryCache(
            max_entries=self._settings.CACHE_MAX_ENTRIES,
            max_entry_bytes=self._settings.CACHE_MAX_ENTRY_BYTES,
            max_memory_bytes=self._settings.CACHE_MAX_MEMORY_BYTES,
            default_ttl_seconds=self._settings.CACHE_DEFAULT_TTL_SECONDS,
        )

    @property
    def is_enabled(self) -> bool:
        # If multi-worker is configured (>1), caching is disabled for safety
        if self._settings.WORKER_COUNT > 1:
            return False
        return self._settings.CACHE_ENABLED

    def get_or_compute(
        self,
        series_id: str | uuid.UUID,
        resource: str,
        compute_fn: Callable[[], T],
        reader_chapter: int | None = None,
        query_params: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
    ) -> T:
        """Retrieves an item from the cache or computes it via the provided callback.

        Guarantees:
        - If cache is disabled, calls compute_fn() directly.
        - If namespace is marked DIRTY, bypasses cache and calls compute_fn().
        - If cache raises any error, logs a warning and degrades safely to compute_fn().
        - Under no circumstances does a cache failure return 500 or corrupt data.
        """
        sid_str = str(series_id)

        # 1. Check if disabled
        if not self.is_enabled:
            return compute_fn()

        # 2. Check if namespace is marked DIRTY
        try:
            if self._backend.is_dirty(sid_str):
                logger.warning(
                    "Cache bypassed: namespace %s is marked DIRTY",
                    sid_str,
                    extra={
                        "event": "cache.dirty",
                        "series_id": sid_str,
                        "resource": resource,
                        "reader_chapter": reader_chapter,
                    },
                )
                return compute_fn()
        except Exception as e:
            logger.error("Cache backend error during is_dirty check: %s", e)
            return compute_fn()

        # 3. Build Key
        key = build_cache_key(
            version=self._settings.CACHE_VERSION,
            series_id=series_id,
            resource=resource,
            reader_chapter=reader_chapter,
            query_params=query_params,
        )

        # 4. Attempt Cache Read
        start_time = time.perf_counter()
        try:
            cached_value = self._backend.get(key)
            if cached_value is not None:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 3)
                logger.info(
                    "Cache HIT for %s in %sms",
                    key,
                    duration_ms,
                    extra={
                        "event": "cache.hit",
                        "key": key,
                        "series_id": sid_str,
                        "resource": resource,
                        "reader_chapter": reader_chapter,
                        "duration_ms": duration_ms,
                        "outcome": "hit",
                    },
                )
                return cached_value
        except Exception as e:
            logger.error(
                "Cache read error for key %s: %s (degrading to DB compute)",
                key,
                e,
                extra={"event": "cache.error", "key": key, "error": str(e)},
            )
            return compute_fn()

        # 5. Cache Miss -> Compute Canonical Result
        duration_ms = round((time.perf_counter() - start_time) * 1000, 3)
        logger.info(
            "Cache MISS for %s",
            key,
            extra={
                "event": "cache.miss",
                "key": key,
                "series_id": sid_str,
                "resource": resource,
                "reader_chapter": reader_chapter,
                "outcome": "miss",
            },
        )

        computed = compute_fn()

        # 6. Attempt Cache Write
        try:
            self._backend.set(key, computed, ttl_seconds=ttl_seconds)
        except Exception as e:
            logger.error(
                "Cache write error for key %s: %s",
                key,
                e,
                extra={"event": "cache.error", "key": key, "error": str(e)},
            )

        return computed

    def invalidate_series(self, series_id: str | uuid.UUID) -> int:
        """Invalidates all cached entries for a given series.

        If an exception occurs during invalidation:
        - Marks the series as DIRTY so all subsequent reads bypass the cache.
        - Does NOT re-raise, preventing rollback of committed DB transactions.
        """
        sid_str = str(series_id)
        if not self.is_enabled:
            return 0

        prefix = build_series_prefix(self._settings.CACHE_VERSION, sid_str)
        try:
            count = self._backend.delete_prefix(prefix)
            # Ensure series is marked clean
            self._backend.clean_dirty(sid_str)
            logger.info(
                "Cache invalidated %s entries for series %s (prefix: %s)",
                count,
                sid_str,
                prefix,
                extra={
                    "event": "cache.invalidate",
                    "series_id": sid_str,
                    "deleted_count": count,
                    "outcome": "success",
                },
            )
            return count
        except Exception as e:
            logger.critical(
                "Cache invalidation FAILED for series %s: %s. Marking namespace DIRTY.",
                sid_str,
                e,
                extra={
                    "event": "cache.invalidate.failure",
                    "series_id": sid_str,
                    "error": str(e),
                    "outcome": "dirty_bypass",
                },
            )
            try:
                self._backend.mark_dirty(sid_str)
            except Exception as dirty_err:
                logger.error("Failed to mark namespace DIRTY: %s", dirty_err)
            return 0

    def clean_series(self, series_id: str | uuid.UUID) -> None:
        """Removes the dirty status for a series."""
        try:
            self._backend.clean_dirty(str(series_id))
        except Exception:
            pass

    def clear(self) -> None:
        """Clears all cached entries and dirty namespaces."""
        try:
            self._backend.clear()
        except Exception as e:
            logger.error("Failed to clear cache: %s", e)

    def stats(self) -> dict[str, Any]:
        """Returns cache stats."""
        try:
            return self._backend.stats()
        except Exception as e:
            return {"error": str(e)}


_default_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    global _default_cache_service
    if _default_cache_service is None:
        _default_cache_service = CacheService()
    return _default_cache_service


def reset_cache_service_for_testing(
    new_service: CacheService | None = None,
) -> CacheService | None:
    """Helper to inject or reset cache service during testing."""
    global _default_cache_service
    _default_cache_service = new_service
    return _default_cache_service
