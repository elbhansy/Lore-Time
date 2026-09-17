# Phase 4.8 — Cache Architecture Decision

## 1. Context & Problem Statement

The Temporal Story Intelligence platform requires low-latency queries for computationally intensive workloads (such as WorldState reconstruction and analytics aggregation across thousands of canonical events) while maintaining an uncompromising temporal spoiler firewall (`readerChapter`).

We evaluate four architectural options against the strict criteria of correctness, temporal isolation, operational simplicity, and measured performance benefit.

---

## 2. Evaluation of Architectural Options

### Option A: No Cache (Database-Only)
- **Mechanism**: Every query executes directly against PostgreSQL 18.
- **Pros**: Zero cache-invalidation bugs, perfect consistency, zero memory footprint.
- **Cons**: 10K-event WorldState rebuilds take 37.55ms; analytics take ~68ms (P95: 307ms). Under high read traffic, database CPU saturates rebuilding identical historical states.
- **Verdict**: Inadequate for high-concurrency production reading traffic.

### Option B: In-Process Bounded LRU Cache (SELECTED)
- **Mechanism**: Thread-safe in-memory LRU cache inside the application process with deterministic namespacing, strict entry size bounds (`CACHE_MAX_ENTRY_BYTES`), maximum entries (`CACHE_MAX_ENTRIES`), and global memory ceiling (`CACHE_MAX_MEMORY_BYTES`).
- **Pros**:
  - **Zero Network Overhead**: Cache hit latency is < 0.05ms (vs 1-2ms network round-trip for Redis).
  - **Zero Speculative Infrastructure**: No external Redis, Sentinel, or distributed lock management required.
  - **Simplicity & Reliability**: Failure degradation is transparent; if in-process lookup fails, it simply queries PostgreSQL.
- **Cons & Constraints**:
  - **Process-Local Scope**: Each OS process has an independent cache.
  - **Multi-Worker Policy**: In a multi-worker deployment, in-process caches cannot guarantee cross-process cache synchronization without distributed pub/sub.
  - **Deployment Policy**: Explicitly enforced policy: `CACHE_ENABLED=true` is supported **only for single-process deployments**. In multi-worker deployments, caching is disabled or unsupported.
- **Verdict**: **APPROVED & SELECTED**. Solves the latency bottleneck with minimal complexity and maximum speed.

### Option C: External Distributed Cache (e.g. Redis)
- **Mechanism**: Central Redis cluster queried over TCP.
- **Pros**: Shared cache across multiple worker processes.
- **Cons**:
  - Requires deploying, monitoring, securing, and backing up external Redis instances.
  - Network hop overhead (1–2ms latency, negating 90% of in-memory speedup).
  - JSON/pickle serialization/deserialization overhead.
  - Vulnerable to network partitions, connection pool exhaustion, and distributed cache stampedes.
  - Violates Hard Rules 4, 5, 6, and 8 (no speculative infrastructure without proof of necessity).
- **Verdict**: **REJECTED** for Phase 4.8. Can be implemented as an alternate `CacheBackend` in the future if a multi-node cluster becomes a verified production requirement.

### Option D: Hybrid (L1 In-Process + L2 Redis)
- **Mechanism**: Two-tier caching hierarchy.
- **Pros**: Fast local hits with multi-worker synchronization.
- **Cons**: Extreme operational and invalidation complexity; high risk of cache drift and split-brain temporal leakage.
- **Verdict**: **REJECTED**.

---

## 3. Mandatory Architecture Limitations & Multi-Worker Policy

1. **Architecture Classification**: In-Process Bounded LRU.
2. **Distributed Cache**: NOT IMPLEMENTED.
3. **Multi-Worker Policy**:
   - `CACHE_ENABLED = true` is valid ONLY in a single-process deployment (`WORKER_COUNT=1`).
   - If `WORKER_COUNT > 1` is configured with `CACHE_ENABLED=true`, the application enforces fail-safe behavior: it logs a high-severity configuration alert and disables caching, operating directly against PostgreSQL.
   - We explicitly declare that multiple worker processes have independent caches and do NOT claim cross-process synchronization.
4. **Canonical Source of Truth**: PostgreSQL remains the sole source of truth. Cache loss or cache eviction has zero impact on canonical data integrity.
