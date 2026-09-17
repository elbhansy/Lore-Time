"""Unit tests for BoundedMemoryCache (LRU, entry bytes limits, memory limits, and dirty status)."""

import time

from apps.api.app.core.cache.memory_cache import BoundedMemoryCache


def test_memory_cache_hit_and_miss():
    cache = BoundedMemoryCache(max_entries=10, max_entry_bytes=1000)
    assert cache.get("k1") is None

    cache.set("k1", {"data": "hello"})
    assert cache.get("k1") == {"data": "hello"}

    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["entries"] == 1


def test_memory_cache_rejection_of_oversized_payloads():
    """Payloads exceeding max_entry_bytes must be rejected immediately."""
    cache = BoundedMemoryCache(max_entries=10, max_entry_bytes=100)
    oversized = {"big": "x" * 200}

    stored = cache.set("k_big", oversized)
    assert stored is False
    assert cache.get("k_big") is None

    stats = cache.stats()
    assert stats["rejections"] == 1
    assert stats["entries"] == 0


def test_memory_cache_lru_eviction_on_max_entries():
    """Exceeding max_entries must evict least recently used entries."""
    cache = BoundedMemoryCache(max_entries=3, max_entry_bytes=1000)

    cache.set("k1", "v1")
    cache.set("k2", "v2")
    cache.set("k3", "v3")

    # Access k1 to make it most recently used (order now: k2, k3, k1)
    assert cache.get("k1") == "v1"

    # Add k4 -> should evict k2
    cache.set("k4", "v4")

    assert cache.get("k2") is None  # evicted!
    assert cache.get("k1") == "v1"
    assert cache.get("k3") == "v3"
    assert cache.get("k4") == "v4"

    stats = cache.stats()
    assert stats["evictions"] == 1
    assert stats["entries"] == 3


def test_memory_cache_ttl_expiration():
    cache = BoundedMemoryCache(max_entries=10, default_ttl_seconds=1)
    cache.set("k_exp", "val", ttl_seconds=0.1)

    assert cache.get("k_exp") == "val"
    time.sleep(0.15)
    assert cache.get("k_exp") is None


def test_memory_cache_delete_prefix():
    cache = BoundedMemoryCache(max_entries=100)
    cache.set("v1:seriesA:world_state:ch1:empty", "dataA1")
    cache.set("v1:seriesA:world_state:ch2:empty", "dataA2")
    cache.set("v1:seriesB:world_state:ch1:empty", "dataB1")

    deleted = cache.delete_prefix("v1:seriesA:")
    assert deleted == 2
    assert cache.get("v1:seriesA:world_state:ch1:empty") is None
    assert cache.get("v1:seriesA:world_state:ch2:empty") is None
    # Series B is completely untouched
    assert cache.get("v1:seriesB:world_state:ch1:empty") == "dataB1"


def test_memory_cache_dirty_namespaces():
    cache = BoundedMemoryCache()
    assert not cache.is_dirty("series_123")

    cache.mark_dirty("series_123")
    assert cache.is_dirty("series_123")
    assert not cache.is_dirty("series_456")

    cache.clean_dirty("series_123")
    assert not cache.is_dirty("series_123")
