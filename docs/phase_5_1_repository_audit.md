# Phase 5.1: Repository Audit & Capability Mapping

## 1. Overview & Objective

This document audits the repository assets directly relevant to building the **Phase 5.1 Narrative Intelligence Engine**. It establishes how the existing `WorldState`, `CharacterState`, `EventApplier`, `WorldStateComparator`, and canonical events provide the factual foundation for deriving character arcs, arc milestones, turning points, and narrative phases.

---

## 2. Existing Data Structures & Semantics

### 2.1 Character State (`packages/domain/state/character_state.py`)
- `character_id: EntityId`: Unique character identifier.
- `exists: bool`: Whether character has been introduced by the current chapter.
- `alive: bool`: Mortality state (alive vs dead).
- `rank: Optional[str]`: Current power rank ID.
- `faction_id: Optional[str]`: Active faction affiliation ID.
- `unlocked_skills: Set[str]`: Set of unlocked/active skill IDs.

### 2.2 World State Aggregate (`packages/domain/state/world_state.py`)
- Represents the complete state of a series at chapter $N$.
- Contains `characters: Dict[EntityId, CharacterState]`, `relationships: Dict[Tuple[str, str], RelationshipState]`, `rank_transitions`, `skills`, and `factions`.
- Built purely and deterministically via `WorldStateBuilder.build(series_id, envelopes, reader_chapter)`.

### 2.3 Event Envelope & Ordering (`packages/domain/services/event_ordering.py`)
- Encapsulates `event: Event` and `chapter_number: ChapterNumber`.
- `sort_events(envelopes)` deterministically sorts by `(chapter_number, event.sequence, str(event.id.value))`.

### 2.4 Comparison Engine (`packages/domain/comparison/world_state_comparator.py`)
- Takes `state_a` and `state_b` and returns `TemporalComparison`:
  - `character_changes`: `INTRODUCED`, `REMOVED`, `CHANGED` (status change alive/dead).
  - `power_changes`: `before_rank`, `after_rank`.
  - `skill_changes`: `unlocked_skills`.
  - `relationship_changes`: `CREATED`, `ENDED`, `CHANGED`.

### 2.5 Event Model (`packages/domain/entities/event.py`)
- Contains `type: EventType`, `subject_id: EntityId`, `target_id: Optional[EntityId]`, `chapter_id`, `sequence`, `previous_state`, `new_state`, and `metadata`.
- Event types directly supported:
  - `CHARACTER_INTRODUCED`, `CHARACTER_DIED`
  - `POWER_RANK_CHANGED`
  - `SKILL_UNLOCKED`, `SKILL_UPGRADED`, `SKILL_EVOLVED`, `SKILL_REPLACED`, `SKILL_LOST`
  - `RELATIONSHIP_CREATED`, `RELATIONSHIP_CHANGED`, `RELATIONSHIP_ENDED`
  - `FACTION_INTRODUCED`, `FACTION_MEMBER_JOINED`, `FACTION_MEMBER_LEFT`, `FACTION_LEADER_CHANGED`

---

## 3. Narrative Intelligence Mapping

| Analytical Concept | Domain Derivation Logic | Supporting Canonical Data |
| :--- | :--- | :--- |
| **`ArcMilestone`** | Significant discrete events modifying the character directly or indirectly. | Canonical event stream where `subject_id == char_id` or `target_id == char_id`. |
| **`TurningPoint`** | Milestone or state delta with measurable multi-dimensional impact (e.g. death/resurrection, major power shift, faction defection, enemy formation). | `EventImpactAnalyzer` / `WorldStateComparator` state shift magnitude. |
| **`NarrativePhase`** | Contiguous chapter blocks bounded by turning points or major arc milestones with consistent state characteristics. | Grouping milestone sequences bounded by `TurningPoint` occurrences. |
| **`CharacterArc`** | Temporal trajectory aggregate combining milestones, turning points, and phases up to `readerChapter`. | Complete synthesized analytical aggregate. |

---

## 4. Invariants & Rules

1. **Pure Projection**: Narrative intelligence creates value objects in memory from existing queries. It issues zero `INSERT`, `UPDATE`, or `DELETE` statements.
2. **Strict Firewall**: Only events with `chapter <= reader_chapter` are passed to the builder.
3. **Traceability**: Every milestone and turning point points directly to the backing canonical `event_id` and chapter number.
