# Phase 4.9 — Rate Limiting Architecture Decision

## 1. Context & Architectural Options

We evaluate rate limiting architectures for the Temporal Story Intelligence platform against the primary objectives: protecting PostgreSQL and compute resources, preserving the temporal spoiler firewall, bounding process memory, and avoiding unnecessary infrastructure.

---

## 2. Options Evaluation

### Option A: No Rate Limiting
- **Mechanism**: All client requests are processed without frequency boundaries.
- **Cons**: Vulnerable to trivial resource exhaustion via repeated expensive WorldState rebuilds (37ms each) or analytics queries (68ms each).
- **Verdict**: **REJECTED**.

### Option B: In-Process Bounded Sliding Window Rate Limiter (SELECTED)
- **Mechanism**: Process-local, thread-safe Sliding Window Counter with explicit burst limits per tier, bounded tracked identities (`MAX_IDENTITIES=10000`), bounded timestamps per identity (`MAX_HITS_PER_IDENTITY=100`), LRU eviction of idle keys, and trusted proxy peer verification.
- **Pros**:
  - Sub-microsecond latency (< 0.01ms overhead per request).
  - Zero external dependencies (No Redis, Memcached, or network hops).
  - Bounded memory footprint (< 5 MB RAM maximum).
  - Deterministic HTTP 429 contract with `Retry-After`.
- **Cons & Mitigations**:
  - Process-local scope. Handled by explicit deployment policy: `RATE_LIMIT_ENABLED=true` is supported **only for single-process deployments (`WORKER_COUNT=1`)**.
- **Verdict**: **APPROVED & SELECTED**.

### Option C: External Distributed Limiter (Redis / Memcached)
- **Mechanism**: Central Redis instance storing token buckets or sliding windows over TCP.
- **Cons**:
  - Network round-trip penalty (1-2ms latency added to every API request).
  - Connection pool management and Redis cluster failure risks.
  - Violates Hard Rules 1, 2, and 3 (no speculative distributed infrastructure without necessity).
- **Verdict**: **REJECTED** for Phase 4.9. Can be introduced in Phase 5+ if multi-node distributed clusters become an operational requirement.

### Option D: Hybrid (Local In-Memory + Central Sync)
- **Mechanism**: Two-tier rate limiter.
- **Cons**: High operational complexity, split-brain drift risks, and high debugging overhead.
- **Verdict**: **REJECTED**.

---

## 3. Algorithm Selection: Sliding Window Counter with Explicit Burst

- **Algorithm**: Sliding Window Counter with timestamped deque.
- **Why not Fixed Window?**: Fixed window suffers from boundary burst doubling (e.g. 30 requests at 00:59 followed by 30 requests at 01:00 = 60 requests in 2 seconds).
- **Why not pure Token Bucket?**: Token bucket math can be subtle under burst conditions; explicit (Limit, Burst) sliding window semantics provide deterministic visibility into exact requests within the active window.
- **Contract**:
  $$\text{check}(key, limit, burst) \longrightarrow \text{RateLimitResult}(allowed: \text{bool}, retry\_after: \text{int}, remaining: \text{int})$$
  The middleware consumes this clean contract without coupling to internal algorithm details.
