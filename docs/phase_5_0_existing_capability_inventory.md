# Phase 5.0: Existing Capability Inventory & Reuse Mapping

## 1. Executive Summary

This inventory maps all existing core product intelligence engines across the Temporal Story Intelligence platform (Phases 0–4). The goal is to maximize code reuse, avoid duplicate logic, and ensure that Phase 5 higher-level intelligence capabilities build strictly upon validated, deterministic domain models.

---

## 2. Inventory & Reuse Matrix

| Engine / Subsystem | Location | Responsibility | Inputs | Outputs | Temporal & Series Semantics | Phase 5 Reuse Opportunities | Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`WorldStateBuilder`** | `packages/domain/services/world_state_builder.py` | Reconstructs state at chapter $N$ from event envelopes. | `series_id`, `envelopes`, `reader_chapter` | `WorldState` aggregate | Filters events $> reader\_chapter$, strictly series-isolated. | **Primary foundation**: Base state builder for all narrative and counterfactual branches. | Sequential scan over all envelopes up to $N$. |
| **`EventApplier`** | `packages/domain/services/event_applier.py` | Applies discrete domain events to mutate `WorldState`. | `state: WorldState`, `env: EventEnvelope` | Mutated `WorldState` | Modifies characters, ranks, skills, factions, and relationships. | **Simulation engine**: Reusable for hypothetical scenario propagation and branch replay. | In-memory synchronous mutation. |
| **`WorldStateComparator`** | `packages/domain/comparison/world_state_comparator.py` | Computes state differences between two points in time. | `state_a: WorldState`, `state_b: WorldState` | `TemporalComparison` (character, power, skill, relationship diffs) | Compares any two chapter states. Series must match. | **Delta detector**: Turning point detection, narrative phase transitions, and counterfactual branch diffing. | Compares state snapshots, not event causality directly. |
| **`EventImpactAnalyzer`** | `packages/domain/services/event_impact_analyzer.py` | Evaluates causal consequence of a single event on state. | `event: Event`, `before: WorldState` | `ImpactAnalysisResult` (direct and derived impacts) | Evaluates state shift caused by the isolated event. | **Causal building block**: Step-by-step impact tracing for causal chain construction. | Evaluates single event impact; does not chain multi-event indirect influence. |
| **`TemporalGraphBuilder`** | `packages/domain/services/temporal_graph_builder.py` | Projects `WorldState` into a queryable node-edge graph. | `world_state: WorldState`, `entities: GraphEntities` | `TemporalGraph` (nodes, edges) | Clamps strictly to `reader_chapter`. Drops future entities. | **Projection engine**: Graph views for narrative explorer and relationship clusters. | Read-only projection; is not and must not become source of truth. |
| **`AnalyticsReader`** | `apps/api/repositories/canonical/sqlalchemy_analytics_reader.py` | Aggregates event distributions and character activity over chapter bounds. | `series_id`, `from_chapter`, `to_chapter` | `EventDistribution`, `CharacterActivity` | Bounded by chapter range; series-scoped. | **Quantitative narrative metrics**: Measuring character arc pacing, climax density, and activity spikes. | Database SQL aggregations; does not infer narrative arcs. |
| **`GlobalSearchUseCase`** | `apps/api/app/application/search/global_search.py` | Searches canonical entities, events, and lore with spoiler filtering. | `series_id`, `SearchQuery` (text, type, reader_chapter) | `SearchPageResult` | Future entities/events filtered at chapter horizon. | **Discovery filter**: Foundation for advanced compound discovery queries. | Keyword/prefix search; does not evaluate multi-hop narrative predicates. |
| **`Provenance` & `Evidence`** | `packages/domain/provenance/*` | Records source chapter, text location, and extraction confidence. | Raw fact metadata | `Provenance` value object | Tied to specific chapter and source record. | **Intelligence explainability**: Every inferred arc or causal step links back to canonical evidence. | Static provenance for facts; needs composition for multi-step reasoning. |

---

## 3. Key Reuse Principles for Phase 5

1. **`WorldState` as the Single Source of Truth**: All narrative intelligence, character arcs, and causal analyses must evaluate against `WorldState` snapshots produced by `WorldStateBuilder`.
2. **Immutable Canonical Isolation**: Counterfactual analysis will fork a deep-cloned `WorldState` and replay alternative event streams using `EventApplier`, leaving canonical storage 100% untouched.
3. **Delta-Driven Arc Extraction**: Character arcs will be derived by evaluating sequential diffs from `WorldStateComparator` across major narrative milestones.
