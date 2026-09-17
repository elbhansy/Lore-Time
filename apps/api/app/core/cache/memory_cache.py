"""Thread-safe bounded memory LRU cache implementation."""

import json
import logging
import threading
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger("timeline.cache")


class CacheEntry:
    __slots__ = ("key", "value", "expires_at", "size_bytes")

    def __init__(self, key: str, value: Any, expires_at: float | None, size_bytes: int):
        self.key = key
        self.value = value
        self.expires_at = expires_at
        self.size_bytes = size_bytes

    def is_expired(self, now: float) -> bool:
        return self.expires_at is not None and now > self.expires_at


class BoundedMemoryCache:
    """Thread-safe bounded in-process LRU cache with memory and payload size limits."""

    def __init__(
        self,
        max_entries: int = 5000,
        max_entry_bytes: int = 524288,  # 512 KB
        max_memory_bytes: int = 67108864,  # 64 MB
        default_ttl_seconds: int = 3600,
    ):
        self.max_entries = max_entries
        self.max_entry_bytes = max_entry_bytes
        self.max_memory_bytes = max_memory_bytes
        self.default_ttl_seconds = default_ttl_seconds

        self._lock = threading.RLock()
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._current_memory_bytes: int = 0
        self._dirty_namespaces: set[str] = set()

        # Operational metrics
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0
        self._rejections: int = 0

    def _estimate_size(self, value: Any) -> int:
        """Estimates the memory byte footprint of a cached value."""
        try:
            # Serialized JSON bytes representation provides an exact, deterministic size measurement
            return len(json.dumps(value, default=str).encode("utf-8"))
        except Exception:
            # Fallback estimation
            return 256

    def get(self, key: str) -> Any | None:
        with self._lock:
            now = time.time()
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired(now):
                self._remove_entry(key)
                self._misses += 1
                return None

            # Move to MRU position
            self._entries.move_to_end(key)
            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> bool:
        size_bytes = self._estimate_size(value)

        # Reject oversized payloads
        if size_bytes > self.max_entry_bytes:
            with self._lock:
                self._rejections += 1
            logger.warning(
                "Cache payload rejected: size %s bytes exceeds limit %s bytes for key %s",
                size_bytes,
                self.max_entry_bytes,
                key,
                extra={
                    "event": "cache.rejected",
                    "key": key,
                    "size_bytes": size_bytes,
                    "max_entry_bytes": self.max_entry_bytes,
                },
            )
            return False

        effective_ttl = (
            ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        )
        expires_at = time.time() + effective_ttl if effective_ttl > 0 else None
        entry = CacheEntry(key, value, expires_at, size_bytes)

        with self._lock:
            # If key already exists, deduct previous size
            if key in self._entries:
                self._remove_entry(key)

            # Evict until entry count and memory byte limits are satisfied
            while (
                len(self._entries) >= self.max_entries
                or (self._current_memory_bytes + size_bytes > self.max_memory_bytes)
            ) and self._entries:
                self._evict_lru()

            self._entries[key] = entry
            self._current_memory_bytes += size_bytes
            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._entries:
                self._remove_entry(key)
                return True
            return False

    def delete_prefix(self, prefix: str) -> int:
        with self._lock:
            matching_keys = [k for k in self._entries.keys() if k.startswith(prefix)]
            for k in matching_keys:
                self._remove_entry(k)
            return len(matching_keys)

    def mark_dirty(self, namespace: str) -> None:
        with self._lock:
            self._dirty_namespaces.add(str(namespace))

    def is_dirty(self, namespace: str) -> bool:
        with self._lock:
            return str(namespace) in self._dirty_namespaces

    def clean_dirty(self, namespace: str) -> None:
        with self._lock:
            self._dirty_namespaces.discard(str(namespace))

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._current_memory_bytes = 0
            self._dirty_namespaces.clear()

    def _remove_entry(self, key: str) -> None:
        entry = self._entries.pop(key, None)
        if entry:
            self._current_memory_bytes = max(
                0, self._current_memory_bytes - entry.size_bytes
            )

    def _evict_lru(self) -> None:
        # Pops first item (LRU)
        if self._entries:
            key, entry = self._entries.popitem(last=False)
            self._current_memory_bytes = max(
                0, self._current_memory_bytes - entry.size_bytes
            )
            self._evictions += 1

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (
                round((self._hits / total_requests) * 100, 2)
                if total_requests > 0
                else 0.0
            )
            return {
                "entries": len(self._entries),
                "max_entries": self.max_entries,
                "memory_bytes": self._current_memory_bytes,
                "max_memory_bytes": self.max_memory_bytes,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_pct": hit_rate,
                "evictions": self._evictions,
                "rejections": self._rejections,
                "dirty_namespaces": list(self._dirty_namespaces),
            }
