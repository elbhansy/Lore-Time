# Phase 4.8 — Cache Invalidation Contract

## 1. Invalidation Philosophy: Correctness First

Caching in the Temporal Story Intelligence platform is strictly an optimization. Invalidation is correctness-driven:
1. **Series-Scoped Invalidation**: When a review item is published, all cached entries belonging to the affected `series_id` are invalidated. Unrelated series are completely untouched.
2. **No Global Flushing**: The cache is never indiscriminately wiped on individual events.
3. **Post-Commit Execution**: Cache invalidation occurs strictly **after** the database transaction has successfully committed.
4. **Failure Safety (Dirty Namespace Marking)**: If cache invalidation encounters an exception or fails, the database transaction is **NOT** rolled back. Instead, the affected series namespace is marked as **DIRTY**. All subsequent read requests for that series bypass the cache and read live from PostgreSQL.

---

## 2. Invalidation Lifecycle

```text
[Incoming Review Publication Request]
                 │
                 ▼
     [Start DB Transaction]
                 │
                 ▼
  [Validate, Insert Event, Project Graph, Save Publication Record]
                 │
                 ▼
       [COMMIT TO POSTGRESQL] ──► (Failure? ROLLBACK. Cache untouched. Consistently safe.)
                 │
                 ▼
   [Post-Commit Cache Invalidation]
                 │
        ┌────────┴────────┐
        ▼                 ▼
   [SUCCESS]          [FAILURE]
        │                 │
        ▼                 ▼
[Series Cache Cleared] [Series Namespace Marked DIRTY]
        │                 │
        ▼                 ▼
[Next Read: Cache Miss] [Next Read: Cache Bypassed]
[Recomputes from DB]   [Direct DB Query Executed]
```

---

## 3. Invalidation Rules by Mutation Type

| Mutation Type | Affected Scope | Invalidation Action | Fallback on Invalidation Failure |
| :--- | :--- | :--- | :--- |
| **Canonical Event Publication** | `series_id` | `invalidate_series(series_id)` | Mark `series_id` DIRTY; bypass cache |
| **Entity / Alias Creation** | `series_id` | `invalidate_series(series_id)` | Mark `series_id` DIRTY; bypass cache |
| **Relationship Creation** | `series_id` | `invalidate_series(series_id)` | Mark `series_id` DIRTY; bypass cache |
| **Chapter Addition / Ordering**| `series_id` | `invalidate_series(series_id)` | Mark `series_id` DIRTY; bypass cache |
| **Publication Rollback / Failure**| None | **NO-OP**. Cache untouched. | N/A |
| **Schema Migration / Version Bump**| Global | Bump `CACHE_VERSION` (e.g. `v1` -> `v2`) | Instant logical invalidation across all keys |

---

## 4. Invalidation Failure & Dirty Bypass Invariant

$$\text{PostgreSQL Commit Success} \land \text{Invalidation Failure} \implies \text{Series Marked DIRTY} \implies \text{Bypass Cache} \implies \text{Live DB Query}$$

Under no circumstances will a stale cached entry be served after a failed invalidation attempt.
