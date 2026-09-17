# Phase 4.13: API Surface & Security Audit

## 1. Executive Summary

This document enumerates the complete HTTP API surface for the Timeline Power Visualizer backend. Every registered endpoint is cataloged with its HTTP method, path, rate-limit tier, temporal firewall enforcement, series boundary behavior, and expensive operation classification.

---

## 2. API Endpoint Catalog

| HTTP Method | Route Path | Rate-Limit Tier | Auth Boundary | Temporal Boundary ($N$) | Series Isolation | Expensive Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | **EXEMPT** | Public | None (System liveness) | None | No (O(1) memory) |
| `GET` | `/ready` | **EXEMPT** | Public | None (DB ping `SELECT 1`) | None | No (Lightweight ping) |
| `GET` | `/api/v1/series/{id}/timeline` | **STANDARD_READ** | Public | Clamped to `readerChapter` | Strict `series_id` filter | No (Paginated index query) |
| `GET` | `/api/v1/series/{id}/events` | **STANDARD_READ** | Public | Clamped to `readerChapter` | Strict `series_id` filter | No (Paginated index query) |
| `GET` | `/api/v1/series/{id}/events/{event_id}` | **STANDARD_READ** | Public | Rejects if $> readerChapter$ | Strict `series_id` filter | No (Single row lookup) |
| `GET` | `/api/v1/series/{id}/events/{event_id}/lineage` | **STANDARD_READ** | Public | Rejects if $> readerChapter$ | Strict `series_id` filter | No (Bounded depth traversal) |
| `GET` | `/api/v1/series/{id}/characters` | **STANDARD_READ** | Public | Sanitized enumeration | Strict `series_id` filter | No (Index query) |
| `GET` | `/api/v1/series/{id}/characters/{char_id}` | **STANDARD_READ** | Public | Evaluated at `chapter` | Strict `series_id` filter | No (Single entity state) |
| `GET` | `/api/v1/series/{id}/characters/{char_id}/power-progression` | **STANDARD_READ** | Public | Clamped to `readerChapter` | Strict `series_id` filter | No (Bounded event scan) |
| `GET` | `/api/v1/series/{id}/characters/{char_id}/relationship-history`| **STANDARD_READ** | Public | Clamped to `readerChapter` | Strict `series_id` filter | No (Bounded event scan) |
| `GET` | `/api/v1/series/{id}/characters/{char_id}/relationship-graph` | **EXPENSIVE_READ** | Public | Clamped to `readerChapter` | Strict `series_id` filter | **Yes** (Graph traversal) |
| `GET` | `/api/v1/series/{id}/relationships/graph` | **EXPENSIVE_READ** | Public | Clamped to `readerChapter` | Strict `series_id` filter | **Yes** (Multi-node graph projection) |
| `GET` | `/api/v1/series/{id}/world-state` | **EXPENSIVE_READ** | Public | Strictly computed up to `chapter` | Strict `series_id` filter | **Yes** (Full world-state reconstruction, cached) |
| `GET` | `/api/v1/series/{id}/comparison` | **EXPENSIVE_READ** | Public | Clamped to `readerChapter` | Strict `series_id` filter | **Yes** (Dual-chapter state diff) |
| `GET` | `/api/v1/series/{id}/impact` | **EXPENSIVE_READ** | Public | Clamped to `readerChapter` | Strict `series_id` filter | **Yes** (Causal impact analysis) |
| `GET` | `/api/v1/series/{id}/search` | **EXPENSIVE_READ** | Public | Results $> readerChapter$ discarded | Strict `series_id` filter | **Yes** (Text search + visibility filter) |
| `GET` | `/api/v1/series/{id}/search/suggestions` | **STANDARD_READ** | Public | Future entities discarded | Strict `series_id` filter | No (Prefix match on known entities) |
| `GET` | `/api/v1/series/{id}/power-systems` | **STANDARD_READ** | Public | Evaluated at `chapter` | Strict `series_id` filter | No (Entity lookup) |
| `GET` | `/api/v1/series/{id}/factions` | **STANDARD_READ** | Public | Evaluated at `chapter` | Strict `series_id` filter | No (Entity lookup) |
| `GET` | `/api/v1/series/{id}/skills` | **STANDARD_READ** | Public | Evaluated at `chapter` | Strict `series_id` filter | No (Entity lookup) |
| `GET` | `/api/v1/series/{id}/analytics/*` | **EXPENSIVE_READ** | Public | Aggregations capped at `to_chapter` | Strict `series_id` filter | **Yes** (PostgreSQL aggregation queries) |
| `GET` | `/api/v1/review/queue` | **MUTATING** (Read) | Internal / Admin | N/A (Review pipeline) | Multi-series or scoped | No (Pending review items) |
| `POST`| `/api/v1/review/queue` | **MUTATING** | Internal / Admin | N/A (Review submission) | Payload validated | No (Single item insert) |
| `POST`| `/api/v1/review/items/{id}/publish` | **MUTATING** | Internal / Admin | Atomic publication at `chapter_id` | Strict item series ownership | **Yes** (DB transaction, graph projection, cache flush) |

---

## 3. Security & Boundary Verification

1. **Authentication Boundary Findings**:
   - As documented in Phase 4.5 and confirmed here, read endpoints are intentionally public temporal lore endpoints.
   - Mutating review and publication endpoints (`/api/v1/review/*`) are internal operational surfaces. In production, access to `/api/v1/review/*` must be restricted at the upstream reverse proxy / network layer to authorized internal staff / ingestion workers.
2. **Zero Undocumented Endpoints**:
   - The route tables of `api_router` and `app` match the catalog 100%. No debug, hidden test, or accidental admin endpoints exist in production routes.
3. **No Unbounded Operations**:
   - Every expensive read is classified under the `EXPENSIVE_READ` tier (30 req/min, burst 10) and cached where applicable (`world-state`).
