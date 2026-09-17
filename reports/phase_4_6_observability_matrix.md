# Phase 4.6 — Observability Matrix

## 1. Overview
This matrix verifies that all major operations, use cases, database interactions, and security boundaries across the backend emit standardized, deterministic, and structured lifecycle observability events with correlation and timing.

---

## 2. Comprehensive Observability Matrix

| Operation | Start Event | Success Event | Failure Event | Request ID | Duration | Safe Context | Sensitive Data Risk | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **API HTTP Request** | `request.started` | `request.completed` | `request.failed` | Yes (ContextVar + `X-Request-ID`) | Yes (`duration_ms`) | method, path, status_code | None (Bodies & Auth excluded) | **VERIFIED** |
| **WorldState Build** | - | `world_state.build.completed` | Handled at API layer | Yes (ContextVar) | Yes (`duration_ms`) | series_id, reader_chapter, event_count | None (Future story redacted) | **VERIFIED** |
| **Timeline Query** | `request.started` | `request.completed` | `request.failed` | Yes (ContextVar) | Yes (`duration_ms`) | series_id, from_chapter, to_chapter | None | **VERIFIED** |
| **Global Search** | `request.started` | `request.completed` | `request.failed` | Yes (ContextVar) | Yes (`duration_ms`) | series_id, query, page, page_size | None (Sanitized & bound) | **VERIFIED** |
| **Analytics Query** | `request.started` | `request.completed` | `request.failed` | Yes (ContextVar) | Yes (`duration_ms`) | series_id, from_chapter, to_chapter | None (Scope-level aggregations) | **VERIFIED** |
| **Graph Traversal** | `request.started` | `request.completed` | `request.failed` | Yes (ContextVar) | Yes (`duration_ms`) | series_id, chapter, depth | None (Bounded depth le 3) | **VERIFIED** |
| **Temporal Comparison** | `request.started` | `request.completed` | `request.failed` | Yes (ContextVar) | Yes (`duration_ms`) | series_id, from_chapter, to_chapter | None | **VERIFIED** |
| **Impact Analysis** | `request.started` | `request.completed` | `request.failed` | Yes (ContextVar) | Yes (`duration_ms`) | series_id, event_id, chapter | None | **VERIFIED** |
| **Review / Publish Pipeline** | `review.publish.started` | `review.publish.completed` | `review.publish.rejected` / `rollback` | Yes (ContextVar) | Yes (`duration_ms`) | review_item_id, series_id, resource_type | None (Event payloads excluded) | **VERIFIED** |
| **Canonical Ingestion / Locking** | - | `review.publish.conflict` | Handled in rollback | Yes (ContextVar) | Yes | review_item_id, series_id | None | **VERIFIED** |
| **Database Transaction** | - | `database.transaction.commit` | `database.transaction.rollback` | Yes (ContextVar) | Yes | resource_type, resource_id | None (Raw SQL masked) | **VERIFIED** |
| **Database Operational Failure** | - | - | `database.operation.failed` / `timeout` | Yes (ContextVar) | Yes | error_code, operation | None (Passwords/hosts masked) | **VERIFIED** |
| **Security Temporal Firewall** | - | - | `temporal.boundary_violation` | Yes (ContextVar) | - | requested_chapter, reader_chapter | None (Future story excluded) | **VERIFIED** |
| **Security Validation Failure** | - | - | `validation.failure` | Yes (ContextVar) | - | error_code, url_path | None (Injection sanitized) | **VERIFIED** |
| **Health Liveness & Readiness** | - | Liveness: 200, Readiness: 200 | `database.connection.failure` (503) | Yes (ContextVar) | Yes | status, service, database | None | **VERIFIED** |
