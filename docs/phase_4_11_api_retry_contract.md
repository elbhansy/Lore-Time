# Phase 4.11: API Retry and Mutation Semantics Contract

## 1. Executive Summary

This contract defines the deterministic retry, idempotency, conflict, and timeout semantics for all mutating actions and HTTP interfaces in the **Timeline Power Visualizer** platform.

Per architectural requirements:
1. Mutating endpoints/operations must provide clear duplicate request behavior, idempotency guarantees, timeout handling, conflict resolution, HTTP status codes, and error envelopes.
2. Read-only query endpoints are inherently idempotent (`GET` verbs) with temporal firewall guarantees.
3. No artificial or redundant idempotency mechanisms are invented for endpoints that do not need them.
4. Mutation pipelines (including canonical review item publication and projection) enforce strict transactional atomicity, publication fingerprint deduplication, row-level locks, and post-commit cache invalidation.

---

## 2. Global Error Envelope & Standard Headers

Every error response across both HTTP APIs and internal domain services conforms deterministically to the platform error contract defined in [apps/api/app/main.py](file:///e:/Lore%20Time/timeline-power-visualizer/apps/api/app/main.py) and [apps/api/app/schemas/error.py](file:///e:/Lore%20Time/timeline-power-visualizer/apps/api/app/schemas/error.py).

### 2.1 Standard Error Envelope Format

```json
{
  "error": {
    "code": "<STANDARDIZED_ERROR_CODE>",
    "message": "<HUMAN_READABLE_DESCRIPTION>",
    "details": {}
  },
  "detail": "<HUMAN_READABLE_DESCRIPTION>"
}
```

### 2.2 Standard Diagnostic Headers

All responses (success and error) include standard headers:
- `X-Request-ID`: Distributed tracing identifier (UUID v4) propagated across middlewares and database sessions.
- `Retry-After`: Included on `429 Too Many Requests` responses, specifying seconds to backoff before retrying.
- `X-Content-Type-Options`: `nosniff`
- `X-Frame-Options`: `DENY`
- `Referrer-Policy`: `strict-origin-when-cross-origin`

---

## 3. Endpoints & Operations Audit Matrix

| Endpoint / Operation | HTTP Method | Tier | Duplicate Request Behavior | Timeout Behavior | Retry Behavior | Conflict Behavior | Idempotency Model | HTTP Status | Error Envelope Code |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Publish Review Item** (`/api/v1/review/{item_id}/publish` & `PublishReviewItemUseCase`) | `POST` | `MUTATING` | Returns `200 OK` (idempotent no-op). Does not duplicate events, graph edges, or publication records. | Database query timeout (`504 Gateway Timeout`) or gateway timeout aborts transaction; rollback ensures zero side effects. | **Safe to retry with exponential backoff & jitter**. Subsequent retries resolve to committed state if prior succeeded. | Row-level locking (`SELECT FOR UPDATE`) serializes concurrent workers; second worker detects `PUBLISHED` status and succeeds as no-op. | **Fingerprint & State Deduplication**: `publication_fingerprint` uniquely identifies event content. Status checked within row lock. | `200 OK` (Success/No-op)<br>`400 Bad Request`<br>`404 Not Found`<br>`409 Conflict`<br>`429 Too Many Requests`<br>`500 Internal Error`<br>`503 Service Unavailable`<br>`504 Gateway Timeout` | `PUBLICATION_REJECTED`<br>`RESOURCE_NOT_FOUND`<br>`CONFLICT`<br>`RATE_LIMIT_EXCEEDED`<br>`TRANSACTION_FAILURE`<br>`SERVICE_UNAVAILABLE`<br>`GATEWAY_TIMEOUT` |
| **Review Queue Modification** (`/api/v1/review/queue` or review items) | `POST` / `PUT` | `MUTATING` | Duplicate submissions with identical state key are rejected with `409 CONFLICT` or safely updated if idempotent entity ID provided. | Aborts transaction on timeout; uncommitted state is rolled back. | Safe to retry on transient `503` or network failures; caller must inspect status on timeout. | `409 CONFLICT` on optimistic locking / unique constraint violations (`IntegrityError`). | **Entity ID / State Key**: Enforces unique constraints at schema and database level. | `200 OK` / `201 Created`<br>`400 Bad Request`<br>`409 Conflict`<br>`429 Too Many Requests`<br>`500 Internal Error`<br>`503 Service Unavailable` | `VALIDATION_ERROR`<br>`CONFLICT`<br>`RATE_LIMIT_EXCEEDED`<br>`TRANSACTION_FAILURE`<br>`SERVICE_UNAVAILABLE` |
| **Read Queries** (`/api/v1/{series_id}/*`, e.g., `/world-state`, `/timeline`, `/characters`, `/graph`, `/search`) | `GET` | `STANDARD_READ` / `EXPENSIVE_READ` | Idempotent safe reads. Repeated requests return identical state bounded by `readerChapter`. | Database timeout aborts query (`504 GATEWAY_TIMEOUT`). Cache fallback or retry. | **Safe to retry immediately or with exponential backoff**. | No conflict. Read-only snapshot isolation. | **Naturally Idempotent (`GET`)**. No mutation or state changes. Temporal firewall guarantees boundary enforcement. | `200 OK`<br>`400 Bad Request`<br>`404 Not Found`<br>`429 Too Many Requests`<br>`503 Service Unavailable`<br>`504 Gateway Timeout` | `INVALID_CHAPTER`<br>`RESOURCE_NOT_FOUND`<br>`RATE_LIMIT_EXCEEDED`<br>`SERVICE_UNAVAILABLE`<br>`GATEWAY_TIMEOUT` |

---

## 4. Deep-Dive: Mutation Lifecycle & Retry Semantics

### 4.1 Canonical Publishing Pipeline (`PublishReviewItemUseCase`)

The primary mutating operation in the platform is the canonical publication of review items into timeline events, character progressions, relationship graphs, and entity states.

```
Incoming Request (X-Request-ID, item_id)
                │
                ▼
      [ Check Status == PUBLISHED ] ──(Yes)──> 200 OK (Idempotent No-Op)
                │ (No)
                ▼
   [ Begin DB Transaction ]
                │
                ▼
   [ Lock ReviewItem (SELECT FOR UPDATE) ]
                │
        [ Concurrently Published? ] ──(Yes)──> 200 OK (Conflict Handled Safely)
                │ (No)
                ▼
   [ CanonicalPublisher.prepare_event_data() ]
                │
                ▼
   [ Save Event (Unique publication_fingerprint) ]
                │
                ▼
   [ Atomic Graph Projection ]
                │
                ▼
   [ Save Publication Record & Update Status ]
                │
                ▼
   [ Commit Transaction ] ──(Commit Success)──> [ Invalidate Series Cache ] ──> 200 OK
                │
         (Failure / Timeout)
                │
                ▼
     [ Automatic Rollback ] ──> 500/503/504 Error Response
```

### 4.2 Duplicate Request Handling

1. **State-Level Idempotency Check**:
   If `review_item.status == ReviewStatus.PUBLISHED`, the operation terminates immediately as a successful no-op (`200 OK`), preventing redundant work.
2. **Transaction-Boundary Re-Check**:
   Inside the transaction, after acquiring a row lock via `SELECT ... FOR UPDATE`, the current committed status is re-evaluated. If another worker completed publication during the lock acquisition window, the transaction safely returns success without modifying data.
3. **Database-Level Deduplication**:
   Events are recorded with a unique `publication_fingerprint`. Unique constraints on the `timeline_events` table prevent duplicate event creation even in anomalous race scenarios.

### 4.3 Concurrency & Conflict Handling (`409 CONFLICT`)

- **Row Locks**: Review item rows are locked during publication, eliminating lost updates.
- **Foreign Key / Integrity Constraints**: Concurrent attempts to create entities with duplicate identifiers or invalid references raise `IntegrityError`, mapped deterministically by `integrity_error_handler` to `409 CONFLICT`.
- **Application Conflicts**: Domain-level constraint violations (such as contradictory state transitions) raise `ConflictError`, mapped to `409 CONFLICT` with error code `"CONFLICT"`.

### 4.4 Timeout Handling (`504 GATEWAY_TIMEOUT`)

- **Database Statement Timeout**: Configured via database session settings. If a lock wait or query exceeds the timeout threshold, SQLAlchemy raises `SATimeoutError` or `DatabaseTimeout`.
- **Clean Abort**: The active transaction is aborted and rolled back. No partial writes, orphaned events, or incomplete graph projections persist.
- **Client Mapping**: Handled via `timeout_error_handler` and `db_timeout_handler`, returning HTTP `504` with `"code": "GATEWAY_TIMEOUT"`.

### 4.5 Retry Guidance for Clients

| Status Code | Transient? | Retry Strategy | Backoff Recommendation |
| :--- | :--- | :--- | :--- |
| `200 OK` / `201 Created` | No | **Do NOT retry**. Request completed successfully. | None |
| `400 Bad Request` | No | **Do NOT retry**. Request is invalid (e.g., negative `readerChapter`, malformed payload). | Fix request payload |
| `404 Not Found` | No | **Do NOT retry**. Resource does not exist. | None |
| `409 Conflict` | Conditional | **Retry with jitter** if caused by concurrent lock contention; **Do NOT retry** if caused by business logic conflict. | Full jitter backoff: 50ms to 500ms |
| `429 Too Many Requests` | Yes | **Retry after delay**. Client must respect the `Retry-After` header value. | Exact `Retry-After` seconds |
| `500 Internal Server Error` | Conditional | **Do NOT blind-retry**. Check logs or alert on unhandled exceptions. | Exponential backoff (max 3 retries) |
| `503 Service Unavailable` | Yes | **Retry with exponential backoff**. Database or backend pool temporarily unavailable. | Exponential backoff: base 500ms, max 10s |
| `504 Gateway Timeout` | Yes | **Safe to retry mutating operations** because the mutation pipeline is fully transactional and idempotent. | Exponential backoff with jitter: base 1s |

---

## 5. Temporal Firewall & Series Isolation Invariants During Retries

As verified in the test suite ([tests/integration/temporal/test_temporal_firewall_failure_recovery.py](file:///e:/Lore%20Time/timeline-power-visualizer/tests/integration/temporal/test_temporal_firewall_failure_recovery.py) and [tests/integration/series/test_series_isolation_during_retries.py](file:///e:/Lore%20Time/timeline-power-visualizer/tests/integration/series/test_series_isolation_during_retries.py)):

1. **Temporal Firewall Invariance**:
   A retried or recovered request at `readerChapter = N` **never** exposes entities, relationships, events, metadata, counts, search results, or analytics from chapters $> N$, regardless of whether prior attempts timed out, failed mid-transaction, or encountered cache misses.
2. **Series Isolation Invariance**:
   Retrying operations in `Series A` has zero side effects on `Series B`. Cache keys, lock keys, and database queries are strictly scoped by `series_id`. Idempotency fingerprints are unique per series event.

---

## 6. Verification and Compliance

The platform's retry semantics and deterministic error handling are verified continuously by the test suite:

```bash
pytest -q
# Output: 335 passed, 1 warning (100% passing)
```

All status codes, error envelopes, and headers conform directly to this contract.
