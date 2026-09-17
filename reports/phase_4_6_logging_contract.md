# Phase 4.6 — Structured Logging Contract

## 1. Specification Overview

This contract establishes the canonical schema and rules for structured logging across the Temporal Story Intelligence backend. All log records emitted by the application must conform to this schema, ensuring uniform ingestibility by log aggregation agents while preserving zero leakage of secrets or future story content.

---

## 2. Canonical Log Schema

Each log record is structured as a JSON-serializable dictionary with standard top-level fields.

```json
{
  "timestamp": "2026-09-04T21:30:00.123456Z",
  "level": "INFO",
  "event": "request.completed",
  "service": "timeline-api",
  "environment": "production",
  "request_id": "c1f8a84b-9e45-42f2-8926-079712a6f23a",
  "operation": "get_world_state",
  "duration_ms": 14.8,
  "status_code": 200,
  "series_id": "a0000000-0000-0000-0000-000000000001",
  "resource_type": "world_state",
  "resource_id": null,
  "chapter": null,
  "reader_chapter": 10,
  "error_code": null,
  "outcome": "success",
  "details": {}
}
```

---

## 3. Field Classification

### 3.1 Required Base Fields
Every log record must contain:
1. `timestamp`: ISO-8601 UTC timestamp with microsecond precision.
2. `level`: One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
3. `event`: Canonical dot-separated event identifier (e.g., `request.started`, `request.completed`, `operation.completed`, `security.boundary_violation`).
4. `service`: Constant identifier (defaults to `"timeline-api"`).
5. `environment`: Operating environment (`development`, `test`, `production`).

### 3.2 Optional Contextual Fields
Emitted when applicable to the execution context:
1. `request_id`: Correlation UUID associated with the incoming HTTP request.
2. `operation`: High-level operation or use case name (e.g. `get_world_state`, `global_search`, `publish_review_item`).
3. `duration_ms`: Duration of the measured block/request in milliseconds, rounded to 2 decimal places.
4. `status_code`: HTTP status code (for HTTP request events).
5. `series_id`: String UUID of the tenant/series involved.
6. `resource_type`: Domain entity or aggregate type (e.g. `character`, `power_system`, `event`, `review_item`).
7. `resource_id`: Safe identifier of the target resource.
8. `chapter`: Chapter number associated with the resource.
9. `reader_chapter`: Reader's current chapter horizon for temporal firewall isolation.
10. `error_code`: Standardized application error code (e.g., `RESOURCE_NOT_FOUND`, `INVALID_CHAPTER`, `CONFLICT`).
11. `outcome`: One of `success`, `failure`, `rejected`, `denied`.
12. `details`: Safe key-value dictionary containing non-sensitive context.

---

## 4. Forbidden Fields & Values

Under NO circumstances may the following data appear in any log record, whether in top-level fields, messages, or nested `details`:

| Category | Prohibited Items |
| :--- | :--- |
| **Credentials & Secrets** | `password`, `secret`, `token`, `SECRET_KEY`, `api_key` |
| **Authentication Artifacts** | `Authorization` header contents, `Bearer` tokens, `Cookie`, session IDs |
| **Database Credentials** | Unmasked `DATABASE_URL` with password (must be masked as `:****@`) |
| **Raw Request Bodies** | Full unparsed request bodies or large unvalidated JSON payloads |
| **Future Story Data** | Any entity names, power descriptions, event text, or relationship changes belonging to `chapter > reader_chapter` |
| **Client-Exposed Stack Traces** | Full Python traceback strings in client error payloads |

---

## 5. Standard Event Names

### 5.1 Request Lifecycle
- `request.started`
- `request.completed`
- `request.failed`

### 5.2 Application Operations
- `world_state.build.started` / `world_state.build.completed` / `world_state.build.failed`
- `timeline.query.completed`
- `search.completed`
- `analytics.query.completed`
- `graph.query.completed`
- `comparison.query.completed`
- `impact.query.completed`

### 5.3 Publishing & Ingestion
- `review.publish.started`
- `review.publish.completed`
- `review.publish.rejected`
- `review.publish.conflict`
- `review.publish.rollback`

### 5.4 Database & Persistence
- `database.operation.failed`
- `database.transaction.rollback`
- `database.connection.failure`

### 5.5 Security & Boundary Enforcement
- `cross_series.access_denied`
- `temporal.boundary_violation`
- `invalid_resource.access`
- `publication.authorization_failure`
- `malformed_request`
