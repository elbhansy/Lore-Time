"""Unit tests for SlidingWindowRateLimiter."""

import time

from apps.api.app.core.rate_limit.sliding_window_counter import SlidingWindowRateLimiter


def test_sliding_window_allows_within_limits():
    limiter = SlidingWindowRateLimiter(
        max_identities=100, max_hits_per_identity=50, window_seconds=60
    )
    for i in range(5):
        res = limiter.check("client1", limit=10, burst=5)
        assert res.allowed is True
        assert res.remaining == 10 - (i + 1)
        assert res.retry_after == 0


def test_sliding_window_enforces_window_limit():
    limiter = SlidingWindowRateLimiter(
        max_identities=100, max_hits_per_identity=50, window_seconds=2
    )
    # Burst 10, Limit 5
    for _ in range(5):
        res = limiter.check("client1", limit=5, burst=10)
        assert res.allowed is True

    # 6th request exceeds limit
    res6 = limiter.check("client1", limit=5, burst=10)
    assert res6.allowed is False
    assert res6.remaining == 0
    assert res6.retry_after >= 1

    # After window expiration, client can make requests again
    time.sleep(2.1)
    res_after = limiter.check("client1", limit=5, burst=10)
    assert res_after.allowed is True


def test_sliding_window_enforces_burst_limit():
    limiter = SlidingWindowRateLimiter(
        max_identities=100, max_hits_per_identity=50, window_seconds=60
    )
    # Window limit is 100, but burst is 3
    for _ in range(3):
        res = limiter.check("client_burst", limit=100, burst=3)
        assert res.allowed is True

    # 4th burst request within 5 seconds is blocked
    res_blocked = limiter.check("client_burst", limit=100, burst=3)
    assert res_blocked.allowed is False
    assert res_blocked.retry_after >= 1


def test_sliding_window_bounds_identities_and_evicts_lru():
    """When max_identities is reached, inactive or oldest identities are evicted."""
    limiter = SlidingWindowRateLimiter(
        max_identities=3, max_hits_per_identity=10, window_seconds=60
    )

    limiter.check("ip1", limit=10, burst=5)
    limiter.check("ip2", limit=10, burst=5)
    limiter.check("ip3", limit=10, burst=5)

    stats = limiter.stats()
    assert stats["active_identities"] == 3

    # Add 4th IP -> evicts ip1
    limiter.check("ip4", limit=10, burst=5)

    stats = limiter.stats()
    assert stats["active_identities"] == 3
    assert stats["evictions"] == 1


def test_sliding_window_bounds_hits_per_identity():
    """Deque maxlen strictly caps stored timestamps per identity."""
    limiter = SlidingWindowRateLimiter(
        max_identities=10, max_hits_per_identity=5, window_seconds=60
    )

    for _ in range(20):
        limiter.check("ip_high_hit", limit=50, burst=50)

    record = limiter._identities["ip_high_hit"]
    assert len(record.timestamps) <= 5
