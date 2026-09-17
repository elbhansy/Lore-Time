# Phase 4.8 — Operations & Resources Cacheability Matrix

## 1. Executive Summary

This matrix audits and classifies every major backend operation and resource in the Temporal Story Intelligence platform for caching suitability.

### Classification Categories:
1. **CACHEABLE**: The resource is computationally expensive, deterministic, and its visibility boundary is fully parameterizable. It can be safely cached under strict keying (`series_id`, `readerChapter`, canonical query hash) and series-scoped invalidation.
2. **CONDITIONALLY_CACHEABLE**: The resource is cacheable only if specific boundary conditions are met (e.g. valid `readerChapter`, single-series context, deterministic filters), or if cached with short TTLs and explicit invalidation.
3. **DO_NOT_CACHE**: The resource is transactional, contains active write queues, mutates state, or must reflect instantaneous committed database rows (e.g. review queue, publication records, transactional health checks).

---

## 2. Comprehensive Operation Audit

| Operation / Resource | Endpoint / Service | Classification | Cache Key Factors | Invalidation Trigger | Security & Temporal Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WorldState Rebuild** | `GET /series/{id}/world-state?chapter=N` | **CACHEABLE** | `series_id`, `readerChapter` | Canonical publication for `series_id` | Rebuilding character & relationship state across thousands of events is CPU/DB intensive (~38ms at 10K events). Strict `readerChapter` in key ensures zero spoiler leakage. |
| **Timeline Envelopes** | `GET /series/{id}/timeline?reader_chapter=N&from=A&to=B` | **CACHEABLE** | `series_id`, `readerChapter`, `from`, `to` | Canonical publication for `series_id` | Read-only slice of event envelopes. Bound to `readerChapter`. |
| **Temporal Search** | `POST /series/{id}/search` | **CACHEABLE** | `series_id`, `readerChapter`, canonical query hash | Canonical publication for `series_id` | Search vectors across entities and events. Must encode `readerChapter` so future entities never appear in candidate lists or ranking. |
| **Analytics Summaries** | `GET /series/{id}/analytics` | **CACHEABLE** | `series_id`, `readerChapter`, metric query hash | Canonical publication for `series_id` | Aggregate stats across chapters/events (~68ms at 10K events). Deterministic given canonical events up to `readerChapter`. |
| **Character Profile** | `GET /series/{id}/characters/{char_id}?chapter=N` | **CONDITIONALLY_CACHEABLE** | `series_id`, `char_id`, `readerChapter` | Canonical publication for `series_id` | Character state at chapter $N$ is derived from WorldState. Cacheable if scoped by `readerChapter`. |
| **Character Relationships** | `GET /series/{id}/relationships?chapter=N` | **CONDITIONALLY_CACHEABLE** | `series_id`, `readerChapter` | Canonical publication for `series_id` | Relationship topology active at chapter $N$. |
| **Relationship Graph** | `GET /series/{id}/graph?chapter=N` | **CONDITIONALLY_CACHEABLE** | `series_id`, `readerChapter` | Canonical publication for `series_id` | Graph projection cache tables already exist; in-process cache provides sub-millisecond API response. |
| **Faction Intelligence** | `GET /series/{id}/factions` | **CONDITIONALLY_CACHEABLE** | `series_id`, `readerChapter` | Canonical publication for `series_id` | Faction membership changes over time. Cacheable only with `readerChapter`. |
| **Skill Intelligence** | `GET /series/{id}/skills` | **CONDITIONALLY_CACHEABLE** | `series_id`, `readerChapter` | Canonical publication for `series_id` | Unlocked skills depend on temporal chapter boundary. |
| **Power Intelligence** | `GET /series/{id}/power` | **CONDITIONALLY_CACHEABLE** | `series_id`, `readerChapter` | Canonical publication for `series_id` | Power rankings and progression. |
| **Series Metadata** | `GET /series/{id}` | **CACHEABLE** | `series_id` | Series update | Slowly changing dimension (title, total chapters, description). |
| **Canonical Event Retrieval** | Direct Repository Read | **CONDITIONALLY_CACHEABLE** | `series_id`, `readerChapter`, `event_id` | Canonical publication for `series_id` | Immutable once published, but visibility depends on `readerChapter >= event.chapter`. |
| **Provenance Retrieval** | `GET /sources/{id}` | **CACHEABLE** | `source_id` | Source update | External reference source; static and immutable. |
| **Review Queue** | `GET /review/queue` | **DO_NOT_CACHE** | N/A | N/A | Review queue is a mutable operational workflow. Must reflect instantaneous committed state to prevent concurrent review conflicts. |
| **Publication Records** | Direct Publication Check | **DO_NOT_CACHE** | N/A | N/A | Idempotency and publication checks must inspect live committed database rows. |
| **Health / Ready Checks** | `GET /health`, `GET /ready` | **DO_NOT_CACHE** | N/A | N/A | Liveness and persistence readiness probes must execute live checks against memory and PostgreSQL. |

---

## 3. Strict Boundary Rules

1. **Temporal Parameter Requirement**: No temporal resource (WorldState, timeline, search, relationships, analytics) may be cached without `readerChapter` embedded in the cache key.
2. **Series Isolation**: Every cache key must include `series_id` as the top-level namespace partition.
3. **Dirty Namespace Bypass**: If cache invalidation encounters any failure, the entire `series_id` namespace is marked dirty, bypassing the cache until verified clean.
