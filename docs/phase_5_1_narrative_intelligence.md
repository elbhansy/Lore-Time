# Phase 5.1 — Narrative Intelligence Engine Specification & Documentation

## 1. Executive Summary

Phase 5.1 delivers the first concrete capability of the Advanced Story Intelligence architecture designed in Phase 5.0: the **Narrative Intelligence Engine**. 

The engine derives deterministic narrative structures—such as character arcs, canonical milestones, turning points, narrative phases, and trajectory summaries—from the canonical temporal event stream and WorldState snapshots.

### Core Architectural Principles:
1. **Source of Truth**: `WorldState` remains the singular temporal authority. The Narrative Intelligence Engine is an analytical projection and does NOT introduce a second canonical model or duplicate state representations.
2. **Zero Fictional Generation**: No LLMs, probabilistic heuristics, or speculative text generation are used. All results are analytical deductions backed strictly by canonical evidence.
3. **Zero Speculative Infrastructure**: Implemented cleanly using existing in-process architecture (no Redis, Celery, Kafka, RabbitMQ, or Neo4j).
4. **Strict Decoupling**: Domain models and services have zero dependencies on FastAPI, SQLAlchemy, PostgreSQL, or web frameworks.
5. **Absolute Temporal Security**: For any query parameter `chapter = N` (`readerChapter`), the engine operates strictly within $chapter \le N$. Any event, milestone, transition, turning point, or evidence with $chapter > N$ is invisible. Evaluated and verified across $N-1, N, N+1$.
6. **Series Isolation**: Multi-tenant isolation is strictly maintained across queries, operations, and caches.
7. **Deterministic Ordering**: All lists (milestones, turning points, phases) are deterministically sorted with unambiguous tie-breakers ($chapter \text{ ASC}, event\_id \text{ ASC}, milestone\_type \text{ ASC}$).

---

## 2. Domain Models & Value Objects

The narrative domain contracts reside in `packages/domain/narrative/models.py`. All models are frozen/immutable dataclasses.

### 2.1 MilestoneType (Enum)
Supported canonical state transitions:
- `FIRST_APPEARANCE`: Introduction into the canonical timeline.
- `MAJOR_EVENT`: Analytical inclusion of major story actions.
- `RELATIONSHIP_CHANGE`: Formation, mutation, or dissolution of relationships.
- `FACTION_CHANGE`: Joining or leaving a faction.
- `ABILITY_CHANGE`: Unlocking, evolving, upgrading, or losing skills.
- `RANK_CHANGE`: Power rank advancements or setbacks.
- `POWER_CHANGE`: System-level power adjustments.
- `DEATH`: Mortality transition to deceased state.
- `STATE_CHANGE`: General entity status transition.

### 2.2 SignificanceLevel (Enum)
Deterministic classification based on measurable state impact:
- `LOW`: Standard skill unlocking, standard relationship updates.
- `MEDIUM`: Multi-tier rank changes, leadership changes, faction departure.
- `HIGH`: Major rank breakthroughs, faction leadership succession, critical relationship reversals.
- `CRITICAL`: Character death or existential dimension shifts.

### 2.3 TurningPointType (Enum)
- `MORTALITY_EVENT`: Life/death transition.
- `RANK_BREAKTHROUGH`: Power tier promotion.
- `FACTION_TRANSITION`: Affiliation shift.
- `RELATIONSHIP_REVERSAL`: Major relationship alteration.
- `MULTI_DIMENSIONAL_SHIFT`: Simultaneous transitions across multiple facets.

### 2.4 Aggregate Entities
- `ArcMilestone`: Represents an evidence-backed canonical state transition.
  - `milestone_id`: Deterministic identifier (`ms:{character_id}:{chapter}:{event_id}`)
  - `character_id`, `chapter`, `milestone_type`, `title`, `description`, `event_ids`, `dimension`, `significance`
- `TurningPoint`: Represents an analytically significant inflection point.
  - `turning_point_id`: Deterministic identifier (`tp:{character_id}:{chapter}:{event_id}`)
  - `character_id`, `chapter`, `turning_point_type`, `description`, `significance`, `affected_dimensions`, `previous_state`, `new_state`, `evidence_event_ids`
- `NarrativePhase`: A contiguous, non-overlapping temporal segment.
  - `phase_id`: Deterministic identifier (`phase:{character_id}:{phase_number}:{from_chapter}:{to_chapter}`)
  - `character_id`, `phase_number`, `title`, `from_chapter`, `to_chapter`, `milestone_ids`, `turning_point_id`, `dominant_faction`, `rank_at_phase_end`, `is_active_at_horizon`
- `ArcTrajectorySummary`: Analytical summary of trajectory up to `readerChapter`.
- `CharacterArc`: Aggregate root binding all narrative dimensions together.

---

## 3. Extraction Algorithms

### 3.1 Milestone Extraction (`MilestoneExtractor`)
1. Filters visible event envelopes: $envelope.chapter\_number \le reader\_chapter$.
2. Matches character identity across `subject_id` and `target_id`.
3. Maps `EventType` to `MilestoneType` and assigns deterministic significance levels.
4. Preserves exact canonical provenance (`event.id`).
5. Sorts results deterministically: `(chapter, event_id, milestone_type)`.

### 3.2 Turning Point Detection (`TurningPointDetector`)
1. Evaluates state transitions extracted from events:
   - Death events $\rightarrow$ `MORTALITY_EVENT` (`CRITICAL`).
   - Rank promotions $\rightarrow$ `RANK_BREAKTHROUGH` (`HIGH` / `MEDIUM`).
   - Faction shifts $\rightarrow$ `FACTION_TRANSITION` (`MEDIUM` / `HIGH`).
   - Relationship changes $\rightarrow$ `RELATIONSHIP_REVERSAL` (`MEDIUM` / `HIGH`).
   - Multi-event clusters in a single chapter $\rightarrow$ `MULTI_DIMENSIONAL_SHIFT`.
2. Ties every turning point to explicit event evidence IDs.

### 3.3 Narrative Phase Construction (`NarrativePhaseBuilder`)
1. Breaks the character's temporal span into non-overlapping phases:
   - Initial phase begins at character's first appearance chapter.
   - Turning points act as phase boundaries.
   - A trailing phase extends from the last turning point to `readerChapter`.
2. Milestones are deterministically grouped within their enclosing phase boundaries $[from\_chapter, to\_chapter]$.
3. Captures ending state snapshots (rank, faction) from `WorldState`.

### 3.4 Character Arc Assembly (`CharacterArcBuilder`)
Orchestrates the full pipeline:
$$\text{Canonical Envelopes} \xrightarrow{\le N} \text{Milestones} \rightarrow \text{Turning Points} \rightarrow \text{Phases} \rightarrow \text{Trajectory} \rightarrow \text{CharacterArc}$$

---

## 4. Application Orchestration & API Contract

### 4.1 Application Use Case (`GetCharacterArcUseCase`)
- Verifies series existence in `SeriesRepository`.
- Verifies character existence and tenant matching in `CharacterRepository`.
- Queries `EventRepository.get_all_by_series(series_id, to_chapter=reader_chapter)`.
- Builds `WorldState` at `reader_chapter`.
- Derives `CharacterArc` via `NarrativeIntelligenceEngine`.
- Integrates with `CacheService` using cache key `v1:{series_id}:character_arc:{character_id}:ch{reader_chapter}`.

### 4.2 API Endpoint
- **Route**: `GET /api/v1/series/{series_id}/intelligence/character-arc/{character_id}`
- **Query Parameter**: `chapter: int` (required, $\ge 1$)
- **Rate Limit**: Classified under `EXPENSIVE_READ` tier.
- **Errors**:
  - `400 INVALID_CHAPTER`: If chapter $< 1$.
  - `404 RESOURCE_NOT_FOUND`: If series or character does not exist.
  - `429 RATE_LIMIT_EXCEEDED`: If client exceeds burst/sustained limit.

---

## 5. Verification & Security Evidence
- **Temporal Firewall Gate ($N-1, N, N+1$)**: Verified in `test_character_arc_temporal_firewall_n_minus_1_n_n_plus_1`. Any milestone, turning point, or state beyond `readerChapter` is completely omitted.
- **Series Isolation**: Cross-series lookups are strictly rejected with 404.
- **Determinism**: Repeated queries produce identical byte-for-byte JSON representations.
- **Regression Suite**: 376 passed, 0 failed, 0 skipped.
