"""Thread-safe Bounded Sliding Window Counter Rate Limiter."""

import logging
import threading
import time
from collections import OrderedDict, deque
from typing import Any

from .limiter_protocol import RateLimitResult

logger = logging.getLogger("timeline.rate_limit")


class IdentityRecord:
    """Tracks timestamps for a single client key with a strict max-hits ceiling."""

    __slots__ = ("timestamps", "last_seen")

    def __init__(self, max_hits: int):
        self.timestamps: deque[float] = deque(maxlen=max_hits)
        self.last_seen: float = time.time()


class SlidingWindowRateLimiter:
    """Thread-safe bounded in-memory sliding window rate limiter.

    Guarantees:
    - Memory Bounded: Max identities tracked <= max_identities.
    - Identity Deque Bounded: Max timestamps stored per identity <= max_hits_per_identity.
    - Deterministic Eviction: Inactive/expired identities pruned first, followed by LRU eviction.
    - Explicit Burst: Rejection occurs if either burst limit or window limit is exceeded.
    - Zero unbounded memory growth under adversarial traffic.
    """

    def __init__(
        self,
        max_identities: int = 10000,
        max_hits_per_identity: int = 100,
        window_seconds: int = 60,
    ):
        self.max_identities = max_identities
        self.max_hits_per_identity = max_hits_per_identity
        self.window_seconds = window_seconds

        self._lock = threading.RLock()
        self._identities: OrderedDict[str, IdentityRecord] = OrderedDict()

        # Metrics
        self._allowed_count: int = 0
        self._rejected_count: int = 0
        self._evictions_count: int = 0

    def check(self, key: str, limit: int, burst: int) -> RateLimitResult:
        """Evaluates whether key is allowed under (limit, burst) rules."""
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            # 1. Retrieve or create record
            record = self._identities.get(key)
            if record is None:
                # Enforce max identities limit
                if len(self._identities) >= self.max_identities:
                    self._cleanup_or_evict(now)

                record = IdentityRecord(max_hits=self.max_hits_per_identity)
                self._identities[key] = record

            # Update MRU position & timestamp
            self._identities.move_to_end(key)
            record.last_seen = now

            # 2. Prune timestamps older than the active window
            ts_deque = record.timestamps
            while ts_deque and ts_deque[0] <= window_start:
                ts_deque.popleft()

            current_count = len(ts_deque)

            # 3. Check burst and window limit
            # Burst limit is enforced over the recent short sub-window (e.g. 5 seconds) or instant count
            # Here: total requests within current window cannot exceed limit, and burst cannot exceed burst capacity
            if current_count >= limit:
                self._rejected_count += 1
                # Deterministic retry_after based on when the oldest request in the window expires
                oldest_ts = ts_deque[0]
                retry_after = max(1, int(self.window_seconds - (now - oldest_ts)))
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    retry_after=retry_after,
                )

            # Check instant burst allowance (requests within last 5 seconds)
            burst_window_start = now - min(5.0, self.window_seconds)
            recent_burst_count = sum(1 for ts in ts_deque if ts > burst_window_start)
            if recent_burst_count >= burst:
                self._rejected_count += 1
                retry_after = max(1, int(5.0 - (now - ts_deque[-burst])))
                return RateLimitResult(
                    allowed=False,
                    limit=burst,
                    remaining=0,
                    retry_after=retry_after,
                )

            # 4. Allowed: record timestamp
            ts_deque.append(now)
            self._allowed_count += 1
            remaining = max(0, limit - len(ts_deque))
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                retry_after=0,
            )

    def _cleanup_or_evict(self, now: float) -> None:
        """Removes expired identities first; if still full, evicts least-recently-used."""
        window_start = now - self.window_seconds
        keys_to_remove = []

        # Find inactive keys whose last_seen is older than window
        for k, rec in self._identities.items():
            if rec.last_seen < window_start:
                keys_to_remove.append(k)
            if len(keys_to_remove) >= 100:  # Batch prune
                break

        if keys_to_remove:
            for k in keys_to_remove:
                self._identities.pop(k, None)
            return

        # If no expired keys, evict least recently used (first item)
        if self._identities:
            self._identities.popitem(last=False)
            self._evictions_count += 1

    def clear(self) -> None:
        with self._lock:
            self._identities.clear()

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total = self._allowed_count + self._rejected_count
            rejection_rate = (
                round((self._rejected_count / total) * 100, 2) if total > 0 else 0.0
            )
            return {
                "active_identities": len(self._identities),
                "max_identities": self.max_identities,
                "allowed": self._allowed_count,
                "rejected": self._rejected_count,
                "rejection_rate_pct": rejection_rate,
                "evictions": self._evictions_count,
            }
