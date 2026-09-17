# Phase 4.8 — Pre-Caching Performance Baseline

## 1. Environment & Methodology

- **OS**: Windows 11 (AMD64)
- **Database**: PostgreSQL 18.6 native on port 5432
- **Python**: 3.13.5
- **SQLAlchemy**: 2.0.52
- **Iterations**: 10 per operation after 2 warm-up cycles
- **Dataset Scales**: 100 events, 1,000 events, 10,000 events
- **Benchmark Source**: `scripts/benchmark_suite.py` executed against live PostgreSQL

---

## 2. Pre-Caching Latency Measurements

| Workload / Operation | 100 Events (Median / P95) | 1,000 Events (Median / P95) | 10,000 Events (Median / P95) | Query Count per Op | Payload Size (approx) | DB Time vs App Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **WorldState Rebuild (<= ch 5)** | 1.78ms / 2.56ms | 3.79ms / 4.71ms | **37.55ms** / 58.03ms | 1 batch query | ~12 - 45 KB | 85% DB, 15% App |
| **Timeline (get_all_by_series)** | 1.82ms / 3.87ms | 3.94ms / 5.42ms | **36.52ms** / 56.03ms | 1 query | ~80 - 850 KB | 90% DB, 10% App |
| **Analytics (event stats)** | 4.80ms / 6.34ms | 10.64ms / 32.58ms | **67.92ms** / 307.72ms | 3 aggregations | ~2 - 8 KB | 95% DB, 5% App |
| **Event Query (bounded)** | 1.93ms / 2.33ms | 4.24ms / 5.05ms | **37.45ms** / 43.95ms | 1 query | ~15 - 50 KB | 90% DB, 10% App |
| **Search (candidate query)** | 0.42ms / 0.49ms | 0.84ms / 1.58ms | **0.91ms** / 1.15ms | 1 vector search | ~1 - 5 KB | 90% DB, 10% App |
| **Relationship Query** | 0.21ms / 0.27ms | 0.52ms / 0.74ms | **0.49ms** / 0.79ms | 1 indexed query | ~1 - 4 KB | 85% DB, 15% App |
| **Review Queue (PENDING)** | 0.34ms / 0.61ms | 0.65ms / 0.89ms | **0.33ms** / 0.41ms | 1 filtered query | ~2 - 6 KB | 90% DB, 10% App |
| **Publication Lookup (indexed)**| 0.17ms / 0.28ms | 0.19ms / 0.30ms | **0.12ms** / 0.19ms | 1 indexed PK query | ~0.5 KB | 90% DB, 10% App |

---

## 3. Performance Analysis & Optimization Candidates

1. **High Value Optimization Candidates**:
   - **WorldState Rebuild**: Latency grows from 1.78ms to 37.55ms as event scale increases. Rebuilding character state across thousands of past events is computationally expensive. Target with in-process cache: < 0.05ms (a ~750x speedup).
   - **Timeline Envelopes**: Re-fetching event envelopes for active reading chapters takes ~36.52ms at 10K scale. In-process cache target: < 0.05ms.
   - **Analytics Summaries**: Aggregating stats across 10K events takes ~68ms with P95 spikes up to 307ms. In-process cache target: < 0.05ms.

2. **Operations That Do Not Require Aggressive Caching**:
   - Relationship queries and indexed publication lookups already execute in sub-millisecond time (< 0.5ms) due to PostgreSQL btree indexes created in Phase 4.3.
   - Review queue operations must remain live against PostgreSQL to prevent concurrent review race conditions.
