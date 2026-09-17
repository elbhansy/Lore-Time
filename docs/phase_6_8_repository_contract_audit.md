# Phase 6.8 — Repository & Contract Audit: Narrative Intelligence Experience

**Date:** 2026-09-11  
**Phase:** 6.8  
**Scope:** Narrative Intelligence Experience (`/series/:seriesId/narrative`)  
**Status:** AUDIT COMPLETE — READY FOR IMPLEMENTATION  

---

## 1. Executive Summary

This audit evaluates the contracts, read models, endpoints, hooks, and architectural boundaries for implementing **Phase 6.8 — Narrative Intelligence Experience**.

The workspace must expose existing deterministic narrative intelligence derived by Phase 5.1 and Phase 5.4 read models without creating any new backend business logic, inference engines, client-side score synthesizers, or unapproved contracts.

---

## 2. Existing Backend Contracts & Schemas

### 2.1 Phase 5.1 Domain Models (`packages/domain/narrative/models.py`)

1. **`MilestoneType` (StrEnum):**
   - `FIRST_APPEARANCE`
   - `DEATH`
   - `RESURRECTION`
   - `RANK_CHANGE`
   - `SKILL_ACQUIRED`
   - `SKILL_EVOLVED`
   - `SKILL_LOST`
   - `FACTION_JOINED`
   - `FACTION_LEFT`
   - `FACTION_LEADERSHIP`
   - `RELATIONSHIP_FORMED`
   - `RELATIONSHIP_CHANGED`
   - `RELATIONSHIP_SEVERED`
   - `MAJOR_EVENT`

2. **`SignificanceLevel` (StrEnum):**
   - `LOW`
   - `MEDIUM`
   - `HIGH`
   - `CRITICAL`

3. **`TurningPointType` (StrEnum):**
   - `MORTALITY_EVENT` (Death or resurrection)
   - `POWER_BREAKTHROUGH` (Rank jump or high-tier skill evolution)
   - `FACTION_REALIGNMENT` (Joining, leaving, or leading a faction)
   - `RELATIONSHIP_TRANSFORMATION` (Critical allegiance swing)
   - `MULTI_DIMENSIONAL_SHIFT` (2+ state dimensions modified simultaneously)

4. **`ArcMilestone` (Dataclass):**
   - `milestone_id`: `str`
   - `character_id`: `str`
   - `chapter`: `int`
   - `sequence`: `int`
   - `event_id`: `str`
   - `milestone_type`: `MilestoneType`
   - `description`: `str`
   - `previous_state`: `dict[str, Any]`
   - `new_state`: `dict[str, Any]`
   - `is_canonical`: `bool`

5. **`TurningPoint` (Dataclass):**
   - `turning_point_id`: `str`
   - `character_id`: `str`
   - `chapter`: `int`
   - `sequence`: `int`
   - `event_id`: `str`
   - `turning_point_type`: `TurningPointType`
   - `significance`: `SignificanceLevel`
   - `description`: `str`
   - `affected_dimensions`: `list[str]`
   - `previous_state`: `dict[str, Any]`
   - `resulting_state`: `dict[str, Any]`
   - `is_analytical`: `bool`

6. **`NarrativePhase` (Dataclass):**
   - `phase_id`: `str`
   - `character_id`: `str`
   - `phase_number`: `int`
   - `title`: `str`
   - `from_chapter`: `int`
   - `to_chapter`: `int`
   - `milestone_ids`: `list[str]`
   - `turning_point_id`: `str | None`
   - `dominant_faction`: `str | None`
   - `rank_at_phase_end`: `str | None`
   - `is_active_at_horizon`: `bool`

7. **`ArcTrajectorySummary` (Dataclass):**
   - `total_milestones`: `int`
   - `total_turning_points`: `int`
   - `total_phases`: `int`
   - `current_status`: `str`
   - `current_rank`: `str | None`
   - `current_faction`: `str | None`
   - `total_skills_unlocked`: `int`
   - `total_relationships`: `int`
   - `highest_significance`: `SignificanceLevel`

8. **`CharacterArc` (Dataclass Aggregate):**
   - `series_id`: `str`
   - `character_id`: `str`
   - `reader_chapter`: `int`
   - `start_chapter`: `int | None`
   - `end_chapter`: `int | None`
   - `milestones`: `list[ArcMilestone]`
   - `turning_points`: `list[TurningPoint]`
   - `phases`: `list[NarrativePhase]`
   - `trajectory`: `ArcTrajectorySummary | None`

---

## 3. Existing Backend API Endpoints & Read Models

### 3.1 Endpoints Available

| Endpoint | Path | Parameters | Response Schema | Phase |
|---|---|---|---|---|
| **Story Overview** | `GET /api/v1/series/{series_id}/intelligence/overview` | `chapter` | `StoryOverviewReadModel` | Phase 5.4 |
| **Timeline Feed** | `GET /api/v1/series/{series_id}/intelligence/timeline-feed` | `chapter`, `from`, `to`, `limit`, `offset` | `TimelineReadModel` | Phase 5.4 |
| **Character Profile** | `GET /api/v1/series/{series_id}/intelligence/characters/{character_id}/profile` | `chapter` | `CharacterReadModel` | Phase 5.4 |
| **Character Arc** | `GET /api/v1/series/{series_id}/intelligence/character-arc/{character_id}` | `chapter` | `CharacterArcResponse` | Phase 5.1 |
| **Generic Graph** | `GET /api/v1/series/{series_id}/intelligence/graph` | `chapter`, `graph_type` | `GenericGraphReadModel` | Phase 5.4 |

### 3.2 Discovery & Read Model Mapping

- **Story-Level Narrative Discovery:**
  - `StoryOverviewReadModel` provides:
    - `recent_turning_points: list[TurningPointDTO]` (all characters, bounded by `readerChapter`)
    - `active_phases_by_character: dict[str, str]` (mapping of character ID to current phase title)
    - `total_characters_visible`, `total_events_visible`
  - `TimelineReadModel` provides:
    - `milestones: list[ArcMilestoneDTO]` (all canonical milestones up to `readerChapter`)
    - `turning_points: list[TurningPointDTO]` (all turning points up to `readerChapter`)
  - `GenericGraphReadModel` (with `graph_type="relationship"` or `"causal"`) provides:
    - Characters visible at current horizon (`UniversalGraphNode` where `node_type="CHARACTER"`).
- **Target-Specific Deep Narrative Data:**
  - `CharacterArcResponse` (`GET /api/v1/series/{series_id}/intelligence/character-arc/{character_id}?chapter=N`) contains the full `CharacterArc` aggregate:
    - `milestones: list[ArcMilestoneDTO]`
    - `turning_points: list[TurningPointDTO]`
    - `phases: list[NarrativePhaseDTO]`
    - `trajectory: ArcTrajectorySummaryDTO`

---

## 4. Frontend Contracts & Infrastructure Audit

### 4.1 Frontend TypeScript Contracts (`apps/web/src/api/contracts/read-models.ts`)
- Existing:
  - `ArcMilestoneDTO`
  - `TurningPointDTO`
  - `NarrativePhaseDTO`
  - `StoryOverviewReadModel`
  - `TimelineReadModel`
  - `CharacterReadModel`
  - `GenericGraphReadModel`
- Need to Add to contracts:
  - `ArcTrajectorySummaryDTO`
  - `CharacterArcResponse`
  (Direct mirrors of backend `apps/api/app/schemas/narrative.py`)

### 4.2 Query Layer (`apps/web/src/api/queries/intelligence-queries.ts`)
- Need to add method:
  ```ts
  getCharacterArc(seriesId: string, characterId: string, chapter: number, signal?: AbortSignal): Promise<CharacterArcResponse>
  ```
  Points to `/series/${seriesId}/intelligence/character-arc/${characterId}?chapter=${chapter}`.

### 4.3 React Query Hooks (`apps/web/src/features/temporal/queries/useIntelligenceQueries.ts`)
- Need to add hook:
  ```ts
  useCharacterArc(seriesId: string, characterId: string | null, chapter: number, enabled = true)
  ```
  Using stable query key:
  `['intelligence', 'character-arc', seriesId, characterId, chapter]`

---

## 5. Architectural Compliance & Constraints Verification

1. **Temporal Firewall:**
   - Authoritative horizon is `TemporalContext.readerChapter`.
   - Never query or show data with `chapter > readerChapter`.
   - When stepping backward: if an active selection's earliest chapter is after `readerChapter` or if the character is no longer visible, pure render derivation clears `activeTargetId` to `null`.
2. **Zero N+1 Pattern:**
   - On initial render of `/series/:seriesId/narrative`:
     - Load story-level discovery via `useTimelineFeed` or `useStoryOverview` / `useStoryGraph`.
     - Exactly **0** deep character-arc requests.
   - Deep character arc request executes **only** when a character is explicitly selected.
3. **Series Isolation:**
   - All query keys include `seriesId`.
   - All API paths encode `seriesId`.
   - Changing series isolates cache and resets selections.
4. **Inspector Integration:**
   - Summary on page; deep provenance, state deltas, and evidence in `openInspector`.
   - No duplication of deep inspection trees inside the main workspace cards.

---

## 6. Plan of Execution

- **Milestone 6.8.2**: Create `apps/web/src/features/narrative/narrativeAdapters.ts` and unit tests in `apps/web/src/features/narrative/__tests__/narrativeAdapters.test.ts`.
- **Milestone 6.8.3**: Add `CharacterArcResponse` & `ArcTrajectorySummaryDTO` to contracts; add `getCharacterArc` to query service & hook `useCharacterArc`.
- **Milestone 6.8.4**: Implement `NarrativeHeader.tsx`.
- **Milestone 6.8.5**: Implement `NarrativePhaseTimeline.tsx`.
- **Milestone 6.8.6**: Implement `ArcMilestoneTimeline.tsx`.
- **Milestone 6.8.7**: Implement `TurningPointTimeline.tsx`.
- **Milestone 6.8.8 & 6.8.9**: Implement `CharacterArcExplorer.tsx` and `CharacterArcTrajectory.tsx`.
- **Milestone 6.8.10 & 6.8.11**: Implement `NarrativeSelectionSummary.tsx` with `openInspector`.
- **Milestone 6.8.12 & 6.8.13**: Implement `NarrativePage.tsx`, attach to `/series/:seriesId/narrative` in `App.tsx` and add to `Sidebar.tsx`.
- **Milestone 6.8.14–6.8.24**: Integration test suite `NarrativePage.test.tsx`, run full 5 regression gates, and compile final completion report.
