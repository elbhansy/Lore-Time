# Phase 4.12: Request Boundaries & Resource Limits Policy

## 1. Overview

To prevent memory exhaustion, algorithmic complexity attacks, and denial-of-service, the Timeline Power Visualizer API enforces deterministic bounds on all incoming requests, payload sizes, query parameters, and computational workloads.

---

## 2. Resource Limit Boundaries

| Dimension | Boundary Limit | Enforcement Mechanism | Failure Response |
| :--- | :--- | :--- | :--- |
| **Request Body Size** | `1,048,576 bytes` (1 MB) | `request_correlation_and_lifecycle_middleware` via `Content-Length` | HTTP 413 `REQUEST_ENTITY_TOO_LARGE` |
| **Search Query Text** | `100 characters` | FastAPI Query validation in `/search` | HTTP 422 / 400 `VALIDATION_ERROR` |
| **Pagination Page Size** | `1 <= limit <= 100` | FastAPI Query parameter constraints (`le=100`) | HTTP 422 / 400 `VALIDATION_ERROR` |
| **Pagination Offset** | `offset >= 0` | Non-negative integer check | HTTP 422 / 400 `VALIDATION_ERROR` |
| **Chapter Horizon** | `reader_chapter >= 1` | Temporal firewall boundary validator | HTTP 400 `INVALID_CHAPTER` |
| **Chapter Traversal Range** | `to_chapter >= from_chapter` | Range boundary validation; clamped to `reader_chapter` | Clamped or HTTP 400 |
| **Graph Traversal Depth** | `depth <= 2` (or `<= 3` for local neighborhood) | Explicit route parameter constraint | HTTP 422 / 400 `VALIDATION_ERROR` |
| **In-Memory Cache Ceiling** | `64 MB` (max 5,000 entries, 512 KB/entry) | `BoundedMemoryCache` active size check and LRU eviction | Oldest entry evicted |
| **Rate Limit Key Cardinality**| `10,000 unique client IPs` | `SlidingWindowCounter` with LRU key eviction | Oldest idle IP evicted |
| **Rate Limit Deque Size** | `100 hits per identity` | Hard deque ceiling | Oldest timestamp popped |

---

## 3. Rationale & Behavioral Guarantees

1. **Memory Safety**:
   - The combined memory footprint of the rate limiter ($< 5\text{ MB}$) and cache ($< 64\text{ MB}$) guarantees that total process RAM remains strictly bounded under $200\text{ MB}$ under sustained load.
2. **Database Protection**:
   - Pagination upper bounds (`limit <= 100`) ensure PostgreSQL queries never allocate unbounded result sets in memory or saturate serialization buffers.
3. **Temporal Spoiler Defense**:
   - Chapter bounds ensure that requests querying ranges above the reader's authorized horizon cannot force the backend to perform speculative computation over unseen story events.
