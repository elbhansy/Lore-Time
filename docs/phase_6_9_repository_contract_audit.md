# Phase 6.9 — Repository & Contract Audit: Counterfactual / What-If Intelligence Experience

**Date:** 2026-09-11  
**Phase:** 6.9  
**Scope:** Counterfactual / What-If Intelligence Experience (`/series/:seriesId/what-if`)  
**Status:** AUDIT COMPLETE — READY FOR IMPLEMENTATION  

---

## 1. Executive Summary

This audit evaluates the architecture, backend models, read models, endpoints, safety constraints, and frontend integration contracts required for implementing **Phase 6.9 — Counterfactual / What-If Intelligence Experience**.

The workspace allows readers to simulate hypothetical narrative interventions at their current reader horizon ($readerChapter = N$), evaluate the divergence against canonical facts, inspect impacted entities, and safely revert without ever persisting mutations or corrupting canonical cache.

---

## 2. Existing Backend Architectural Contracts (Phase 5.0)

### 2.1 Domain Models Defined in Phase 5.0 (`docs/phase_5_0_counterfactual_model.md`)

1. **`AssumptionType` (StrEnum):**
   - `PREVENT_EVENT`: "What if Event X never happened?"
   - `ALTER_OUTCOME`: "What if Character Y survived Event X?"
   - `INJECT_EVENT`: "What if Skill Z was unlocked early?"

2. **`CounterfactualAssumption`:**
   - `target_event_id: str | None`
   - `target_chapter: int`
   - `assumption_type: AssumptionType`
   - `modification_payload: dict`
   - `justification: str`

3. **`CounterfactualScenario`:**
   - `scenario_id: str`
   - `series_id: str`
   - `base_chapter: int`
   - `reader_chapter: int`
   - `assumption: CounterfactualAssumption`
   - `is_hypothetical: bool = True` (IMMUTABLE SAFETY MARKER)
   - `confidence_score: float`
   - `invalidated_events: list[str]`
   - `state_divergence: TemporalComparison`
   - `narrative_summary: str`

### 2.2 Replay & Divergence Architecture
- **In-Memory Sandboxing:** Sandboxes are ephemeral and deep-clone state in memory.
- **Divergence Engine:** Uses `WorldStateComparator.compare(state_canonical, state_sandbox)` to output a standard `TemporalComparison`.
- **Read-Only / No DB Mutations:** The engine never writes to PostgreSQL and never updates canonical caches.

---

## 3. Existing Backend API Endpoints & Read Models

### 3.1 Relevant Existing Endpoints

| Endpoint | Path | Parameters | Return Schema | Status |
|---|---|---|---|---|
| **Timeline Feed** | `GET /api/v1/series/{series_id}/intelligence/timeline-feed` | `chapter`, `from`, `to`, `limit`, `offset` | `TimelineReadModel` | Production |
| **Generic Graph** | `GET /api/v1/series/{series_id}/intelligence/graph` | `chapter`, `graph_type` | `GenericGraphReadModel` | Production |
| **Story Overview** | `GET /api/v1/series/{series_id}/intelligence/overview` | `chapter` | `StoryOverviewReadModel` | Production |
| **Temporal Comparison** | `GET /api/v1/series/{series_id}/comparison` | `from_chapter`, `to_chapter`, `reader_chapter` | `TemporalComparisonResponse` | Production |
| **Event Impact** | `GET /api/v1/series/{series_id}/events/{event_id}/impact` | `chapter` | `ImpactAnalysisResultDTO` | Production |
| **Impact Timeline** | `GET /api/v1/series/{series_id}/impact-timeline` | `from_chapter`, `to_chapter`, `reader_chapter` | `list[ImpactAnalysisResultDTO]` | Production |
| **Character Profile** | `GET /api/v1/series/{series_id}/intelligence/characters/{id}/profile` | `chapter` | `CharacterReadModel` | Production |

### 3.2 Backend Contract Assessment
- The backend features `TemporalComparisonResponse` (`apps/api/app/schemas/comparison.py`), `EventImpactDTO` (`apps/api/app/schemas/impact.py`), and `TimelineReadModel` (`apps/api/app/schemas/read_models.py`).
- Per Phase 5.0 architecture, counterfactual results are ephemeral comparisons between Canonical State ($readerChapter$) and a Simulated Scenario State.
- Because Phase 5.5 (dedicated backend simulation sandbox POST endpoint) is scheduled after Phase 5.4 in the roadmap, the frontend will:
  1. Use existing `TemporalComparisonResponse` (`GET /series/{seriesId}/comparison?from_chapter=N_prev&to_chapter=N&reader_chapter=N`) and `EventImpact` (`GET /series/{seriesId}/events/{eventId}/impact?chapter=N`) as the canonical divergence baseline.
  2. Implement the full client-side Counterfactual Workspace contracts (`CounterfactualAssumption`, `CounterfactualScenarioDTO`, `HypotheticalComparisonDTO`) strictly matching Phase 5.0 models, with immutable `is_hypothetical: true` stamps.
  3. Support simulation execution through deterministic counterfactual projection using the canonical event stream and impact models up to $readerChapter$.

---

## 4. Safety & Invariant Guarantees

1. **Explicit Hypothetical Labeling:**
   - Every hypothetical entity, metric, diff, and card is visually stamped with `HYPOTHETICAL` and `NOT CANON`.
   - Distinctive amber/violet styling distinguishes hypothetical states from teal/cyan canonical states.
2. **Canonical State Immutability:**
   - Scenario construction and execution are purely read/projection workflows.
   - Zero POST/PUT/DELETE mutations against canonical events or world states.
3. **Cache Isolation:**
   - Hypothetical query keys are partitioned under:
     `['intelligence', 'what-if', seriesId, readerChapter, scenarioHash]`
   - Canonical caches (`overview`, `timeline`, `characters`, `graph`, `causality`, `narrative`) are never overwritten or invalidated on scenario execution.
4. **Temporal Firewall (N-1 / N / N+1):**
   - Scenario interventions are restricted to `target_chapter <= readerChapter`.
   - Stepping backward in reader horizon automatically invalidates interventions and results that reference now-future chapters.
5. **Zero N+1 Query Discipline:**
   - Roster discovery loads lightweight metadata from `GenericGraphReadModel` / `TimelineReadModel`.
   - Exactly **0** character profile requests on initial render.
   - Profile requests occur only upon explicit user navigation.

---

## 5. Implementation Roadmap

- **Milestone 6.9.2**: Contracts & pure adapters (`whatIfContracts.ts`, `whatIfAdapters.ts`).
- **Milestone 6.9.3**: Query & API client layer (`getTemporalComparison`, `getEventImpact`, `useWhatIfData`).
- **Milestone 6.9.4**: Header & Canonical Context Bar (`WhatIfHeader.tsx`, `CanonicalContextBar.tsx`).
- **Milestone 6.9.5 & 6.9.6**: Scenario Builder & Summary (`ScenarioBuilder.tsx`, `ScenarioSummary.tsx`).
- **Milestone 6.9.7 & 6.9.8**: Execution state & Hypothetical Result Workspace (`CounterfactualExecutionState.tsx`, `HypotheticalResultPanel.tsx`).
- **Milestone 6.9.9 & 6.9.10**: Canonical vs Hypothetical Comparison & Impacted Entities (`CounterfactualComparison.tsx`, `HypotheticalImpactList.tsx`).
- **Milestone 6.9.11 & 6.9.12**: Safety/Provenance Panel & Reset (`CounterfactualSafetyPanel.tsx`, `ScenarioReset.tsx`).
- **Milestone 6.9.13 & 6.9.14**: Main Page (`WhatIfPage.tsx`), App routing (`/series/:seriesId/what-if`), and Sidebar integration.
- **Milestone 6.9.15–6.9.24**: Unit & Integration tests (`WhatIfPage.test.tsx`), full 5 regression gates, and final completion report.
