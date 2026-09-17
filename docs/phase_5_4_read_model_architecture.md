# Phase 5.4 — Intelligence Read Model & Query Architecture Documentation

## 1. Executive Summary

Phase 5.4 delivers the **Intelligence Read Model & Query Architecture** for the Temporal Story Intelligence platform.

Following the successful completion of Phases 5.0 through 5.3:
- Phase 5.0: Temporal Knowledge Foundation
- Phase 5.1: Narrative Intelligence & Character Arc Modeling
- Phase 5.2: Advanced Causal Chain Intelligence
- Phase 5.3: Temporal Narrative Causal Synthesis

Phase 5.4 transforms these analytical systems into stable, decoupled, UI-facing **Read Models** and a unified **Intelligence Query Architecture**. It does not generate new intelligence; instead, it establishes the presentation and query boundary required by future web/visualizer frontends.

---

## 2. Architectural Design & Flow

```text
CANONICAL DATA
      ↓
WORLD STATE
      ↓
TEMPORAL INTELLIGENCE
      ↓
NARRATIVE INTELLIGENCE
      ↓
CAUSAL INTELLIGENCE
      ↓
NARRATIVE CAUSAL SYNTHESIS
      ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            PHASE 5.4
    READ / QUERY ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      ↓
UI-FACING READ MODELS
      ↓
REST API (V1)
      ↓
FRONTEND / VISUALIZER CLIENTS
```

---

## 3. UI-Facing Read Models

Defined in `apps/api/app/schemas/read_models.py`:

### 3.1 `TemporalContextReadModel`
Provides standardized temporal boundary metadata for every query:
- `series_id`: Series identifier
- `reader_chapter`: Reader's horizon chapter
- `min_visible_chapter`: Minimum boundary (1)
- `max_visible_chapter`: Maximum visible boundary
- `future_information_excluded`: Always `True`

### 3.2 `PaginationMeta`
Bounded, deterministic pagination contract:
- `limit`, `offset`, `total_count`, `has_more`

### 3.3 `StoryOverviewReadModel`
High-level dashboard aggregate for a series at a specific reader chapter:
- Series identity & title
- Temporal context
- Counters for total visible chapters, events, characters, factions, and relationships
- Recent turning points & events (bounded to last 5–10)
- Active narrative phase by character

### 3.4 `TimelineReadModel`
Chronological event feed with causes/effects attached:
- Temporal range (`from_chapter`, `to_chapter`)
- Event read models with preceding causes and succeeding effects
- Deterministic pagination

### 3.5 `CharacterReadModel`
Character profile projection at the reader chapter:
- Name, existence status (`alive`, `dead`, `unintroduced`), power rank, faction, unlocked skills
- Active relationships count
- Narrative phases, milestones, and turning points reached up to the chapter horizon

### 3.6 `GenericGraphReadModel`
Universal graph visualization model:
- `UniversalGraphNode`: Universal node contract (`id`, `node_type`, `label`, `chapter`, `metadata`)
- `UniversalGraphEdge`: Universal directed edge contract (`edge_id`, `source_id`, `target_id`, `edge_type`, `label`, `weight`, `evidence_summary`)

---

## 4. Query Architecture & Service

### `IntelligenceQueryService` (`apps/api/app/application/intelligence/intelligence_query_service.py`)
- Coordinates repository access, WorldState building, and invocation of Phase 5.1, 5.2, and 5.3 domain services.
- Assembles immutable, deterministic read models.
- Enforces the Temporal Firewall: queries at chapter $N$ exclude all data $> N$.
- Integrates with `CacheService` via composite keys (`series_id`, `resource`, `reader_chapter`, `query_params`).

---

## 5. API Endpoints

Mounted under `/api/v1/series`:
- `GET /api/v1/series/{series_id}/intelligence/overview`
- `GET /api/v1/series/{series_id}/intelligence/timeline-feed`
- `GET /api/v1/series/{series_id}/intelligence/characters/{character_id}/profile`
- `GET /api/v1/series/{series_id}/intelligence/graph`

All endpoints are registered under the `EXPENSIVE_READ` rate limit tier.

---

## 6. Verification & Test Evidence
- **Temporal Firewall Gate ($N-1, N, N+1$)**: Verified across all read models. Historical scopes never leak future milestones, rank changes, or mortality events.
- **Series Isolation**: Cross-series queries strictly return 404 `RESOURCE_NOT_FOUND`.
- **Determinism**: Identical queries yield byte-for-byte identical payloads.
- **Full Suite Regression**: 404 passed, 0 failed, 0 skipped in 27.61s.
