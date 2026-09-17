"""Cache Backend Interface & Protocol definition."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CacheBackend(Protocol):
    """Protocol for cache backends (in-process memory, test mocks, or future remote)."""

    def get(self, key: str) -> Any | None:
        """Retrieve an entry by key. Returns None if key does not exist or expired."""
        ...

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> bool:
        """Store an entry. Returns True if successfully stored, False if rejected (e.g. oversized)."""
        ...

    def delete(self, key: str) -> bool:
        """Delete an entry by exact key. Returns True if deleted, False if not found."""
        ...

    def delete_prefix(self, prefix: str) -> int:
        """Delete all entries starting with the specified prefix. Returns count of deleted entries."""
        ...

    def mark_dirty(self, namespace: str) -> None:
        """Mark a namespace (e.g. series_id) as DIRTY following invalidation failure."""
        ...

    def is_dirty(self, namespace: str) -> bool:
        """Check whether a namespace is currently marked DIRTY."""
        ...

    def clean_dirty(self, namespace: str) -> None:
        """Clear the dirty status for a namespace."""
        ...

    def clear(self) -> None:
        """Clear all entries and reset dirty namespaces."""
        ...

    def stats(self) -> dict[str, Any]:
        """Return operational stats (entries, memory_bytes, hits, misses, etc.)."""
        ...
