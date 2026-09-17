# Phase 5.2 — Advanced Causal Chain Intelligence Documentation

## 1. Executive Summary

Phase 5.2 introduces **Advanced Causal Chain Intelligence** to the Temporal Story Intelligence platform.

While Phase 5.1 answered *"What happened to this entity over time?"* (Character Arc), Phase 5.2 answers:
* *"What happened?"*
* *"What caused it?"*
* *"What did it cause?"*
* *"How did the effect propagate across characters, factions, and powers?"*
* *"Which entities were affected?"*
* *"How strong is the causal relationship?"*
* *"What evidence supports the relationship?"*

### Core Architectural Guarantees:
1. **NO LLM Causality**: All causal deductions are produced deterministically via explicit canonical linkages and state transition rules. No generative models or probabilistic heuristics are used.
2. **Canonical Authority**: Canonical events and WorldStates remain strictly read-only and authoritative. Causal relations are analytical derived projections (`DERIVED ≠ CANONICAL`).
3. **Strict Temporal Ordering & Firewall**: Retrocausality is strictly rejected ($time(A) \le time(B)$). All queries with `readerChapter = N` evaluate events and causal relations strictly at $\le N$, verified across $N-1, N, N+1$.
4. **Series Isolation**: Multi-tenant boundaries are strictly enforced. Causal relations cannot cross series borders.
5. **Deterministic Ordering**: All lists of relations, chains, and explanations are deterministically sorted using explicit tie-breakers.

---

## 2. Target Architecture

```text
                    CANONICAL DATA
                         │
                         ▼
                 ┌───────────────┐
                 │   WorldState  │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ Canonical     │
                 │ Events        │
                 └───────┬───────┘
                         │
             ┌───────────┼────────────┐
             ▼           ▼            ▼
       Event Impact   Relationship   State
        Analysis       Graph         Changes
             │           │            │
             └───────────┼────────────┘
                         ▼
              ┌────────────────────┐
              │ Causal Derivation  │
              │ Engine             │
              └──────────┬─────────┘
                         ▼
              ┌────────────────────┐
              │ Causal Relation    │
              │ Graph              │
              └──────────┬─────────┘
                         ▼
              ┌────────────────────┐
              │ Causal Chain       │
              │ Builder            │
              └──────────┬─────────┘
                         ▼
              ┌────────────────────┐
              │ Causal Intelligence│
              │ Service            │
              └──────────┬─────────┘
                         ▼
              ┌────────────────────┐
              │ API / DTO Layer    │
              └────────────────────┘
```

---

## 3. Domain Model & Contracts

Located in `packages/domain/causality/models.py`. All objects are immutable (`frozen=True`).

### 3.1 CausalRelationType (Closed Enum)
- `DIRECT_CAUSE`: Direct cause-and-effect relationship.
- `INDIRECT_INFLUENCE`: Derived transitive influence across multi-hop paths.
- `STATE_TRANSITION`: Cause rooted in state change (e.g., introduction, mortality).
- `RELATIONSHIP_CONSEQUENCE`: Relationship formation, alteration, or termination.
- `POWER_CONSEQUENCE`: Power rank advancement, skill acquisition, upgrade, or evolution.
- `FACTION_CONSEQUENCE`: Faction joining, leadership succession, or departure.
- `CHARACTER_CONSEQUENCE`: Entity-centric downstream behavioral transition.
- `EVENT_CHAIN`: Sequential causal connection.

### 3.2 CausalDerivationType (Closed Enum)
- `CANONICAL_EXPLICIT`: Directly declared in canonical event metadata (`cause_event_id`).
- `DERIVED_DIRECT`: Inferred from direct state transition / relationship rule.
- `DERIVED_INDIRECT`: Derived transitively across intermediate events.
- `DERIVED_PROPAGATED`: Inferred through multi-entity network propagation.

### 3.3 CausalConfidence (Closed Enum)
- `EXPLICIT`: Direct canonical evidence.
- `STRONG`: Immediate state or lifecycle transition.
- `MODERATE`: Transitive or indirect influence.
- `WEAK`: Distant or low-weight propagation.

### 3.4 Key Entities
- `CausalEvidenceReference`: Provenance record holding `rule_id`, `explanation_code`, `source_event_ids`, `target_event_id`, `temporal_basis`, `state_basis`, `relationship_basis`.
- `CausalRelation`: Directed edge between source and target events with score, affected entities, and evidence.
- `CausalChain`: Ordered sequence of relations representing multi-hop causality with cumulative score and depth.
- `CausalConflict`: Explicit representation of contradictory causes (e.g. multiple distinct death causes).
- `CharacterCausalExplanation`: Character-centered upstream causes, downstream consequences, and chains.

---

## 4. Derivation and Graph Machinery

### 4.1 CausalDerivationEngine (`packages/domain/causality/derivation_engine.py`)
- Extracts explicit causes (`cause_event_id`).
- Extracts character lifecycle and power rank transitions.
- Extracts relationship progression (`CREATED -> CHANGED -> ENDED`).
- Extracts faction affiliation and leadership succession.
- Validates all relations via `TemporalCausalValidator`.

### 4.2 CausalGraph (`packages/domain/causality/causal_graph.py`)
- Directed adjacency representation (`_outgoing`, `_incoming`).
- Cycle detection using deterministic depth-first search.
- Contradiction detection for mutually exclusive causes.

### 4.3 CausalChainBuilder (`packages/domain/causality/chain_builder.py`)
- Bounded downstream chain traversal ($O(\text{branching}^{\text{max\_depth}})$ with cycle prevention).
- Bounded upstream causal chain traversal.
- Derivation of transitive `INDIRECT_INFLUENCE` relations without mutating direct edges.

### 4.4 Impact Scoring Formula
$$\text{impact\_score} = \text{directness} \times \text{confidence} \times \text{entity\_spread} \times \text{transition\_weight}$$

Where:
- Directness: `DIRECT_CAUSE` (1.0), `STATE_TRANSITION` (0.95), `RELATIONSHIP_CONSEQUENCE` (0.9), `POWER_CONSEQUENCE` (0.85), `FACTION_CONSEQUENCE` (0.85), `INDIRECT_INFLUENCE` (0.6).
- Confidence: `EXPLICIT` (1.0), `STRONG` (0.85), `MODERATE` (0.65), `WEAK` (0.4).
- Entity Spread: $\min(1.5, 1.0 + (\text{count} - 1) \times 0.1)$.
- Transition: 1.4 for mortality transitions; 1.0 baseline.

---

## 5. API & Application Integration

### 5.1 Endpoint
- **Route**: `GET /api/v1/series/{series_id}/intelligence/character-causality/{character_id}`
- **Query Parameters**:
  - `chapter`: Reader's current chapter horizon ($\ge 1$).
  - `max_depth`: Traversal depth boundary ($1 \le \text{depth} \le 10$, default 4).
- **Rate Limit Tier**: Classified under `EXPENSIVE_READ`.
- **Cache Key**: `v1:{series_id}:character_causality:{character_id}:d{max_depth}:ch{chapter}`.

---

## 6. Verification Results
- Unit Tests: 5/5 passed.
- API Integration Tests: 6/6 passed.
- Full Suite Regression: 387 passed, 0 failed, 0 skipped.
