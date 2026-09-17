# Phase 5.3 — Temporal Narrative Causal Synthesis Documentation

## 1. Executive Summary

Phase 5.3 implements **Temporal Narrative Causal Synthesis**, the unifying analytical intelligence layer of the Temporal Story Intelligence platform.

Phase 5.1 established deterministic Narrative Intelligence and Character Arc modeling.
Phase 5.2 established Advanced Causal Chain derivation and multi-hop propagation.

Phase 5.3 integrates both systems to answer:
```text
What happened?
        ↓
What changed?
        ↓
What caused the change?
        ↓
How did the effect propagate?
        ↓
How did that propagation alter the character arc?
        ↓
How did it affect the wider narrative?
```

### Core Architectural Guarantees:
1. **Zero LLM Reasoning**: All intelligence, causal links, milestones, and turning points are synthesized deterministically.
2. **No Invented Facts**: Strictly bounded by canonical events, WorldState transitions, and derived causal/narrative intelligence.
3. **Preservation of Epistemic Separation**: Canonical facts, derived relations, and narrative interpretations remain distinct and traceable to provenance.
4. **Temporal Firewall & Isolation**: Respects $readerChapter \le N$ constraints, verified across $N-1, N, N+1$. No future leakage. Multi-tenant series boundaries are absolute.
5. **Deterministic Ordering**: All steps, paths, and explanations follow unambiguous sort keys.

---

## 2. Architecture & Data Flow

```text
                    WORLD STATE
                         │
                         ▼
                 CANONICAL EVENTS
                         │
                         ▼
             TEMPORAL RELATIONSHIP GRAPH
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       NARRATIVE ENGINE      CAUSAL ENGINE
              │                     │
              ▼                     ▼
        CHARACTER ARC          CAUSAL CHAINS
              │                     │
              └──────────┬──────────┘
                         ▼
              PHASE 5.3 SYNTHESIS
                         │
                         ▼
          TEMPORAL NARRATIVE EXPLANATION
```

---

## 3. Domain Models & Contracts

Located in `packages/domain/synthesis/models.py`. All dataclasses are frozen/immutable.

### 3.1 NarrativeExplanationType (Enum)
- `EVENT_NARRATIVE`: Centered on an event's upstream causes and downstream arc effects.
- `CHARACTER_NARRATIVE`: Centered on a character's arc milestones, turning points, and causal triggers.
- `ARC_NARRATIVE`: Centered on an overarching arc structure and phase transitions.

### 3.2 NarrativeImpactDimension (Enum)
- `CHARACTER_IMPACT`: Entity lifecycle and personal changes.
- `RELATIONSHIP_IMPACT`: Relationship creation, alteration, or termination.
- `FACTION_IMPACT`: Affiliation shifts and leadership successions.
- `POWER_IMPACT`: Power rank promotions and skill unlocks/evolutions.
- `STATE_IMPACT`: Physical or existential state transitions.
- `ARC_IMPACT`: Intersects directly with arc milestones or turning points.
- `TEMPORAL_IMPACT`: Baseline chronological progression.

### 3.3 Key Value Objects & Aggregates
- `NarrativeCausalStep`: An atomic causal link with affected entities, impact dimensions, and milestone/turning point intersection.
- `NarrativeCausalPath`: An ordered multi-hop sequence of steps connecting root causes to downstream consequences.
- `TurningPointSynthesis`: Before/after state snapshot, phase transitions, and root causal event triggers.
- `TemporalNarrativeCausalExplanation`: Root aggregate holding narrative steps, paths, turning-point syntheses, conflicts, and impact breakdown.

---

## 4. Synthesis Engine

### 4.1 NarrativeCausalSynthesizer (`packages/domain/synthesis/synthesizer.py`)
- Maps incoming/outgoing causal relations into `NarrativeCausalStep` records.
- Groups multi-hop chains into structured `NarrativeCausalPath` aggregates.
- Identifies turning points triggered by causal events and resolves enclosing narrative phases (`phase_before` vs `phase_after`).
- Preserves contradictions and conflicts without silent resolution.

### 4.2 TemporalNarrativeSynthesisService (`packages/domain/services/temporal_narrative_synthesis_service.py`)
- Orchestrates `CausalIntelligenceService` and `NarrativeIntelligenceEngine`.
- Enforces temporal horizon filtering.
- Exposes clean domain-level APIs for event and character narrative causal explanations.

---

## 5. Application & API Layer

### 5.1 Endpoints
- `GET /api/v1/series/{series_id}/intelligence/event-narrative/{event_id}`
- `GET /api/v1/series/{series_id}/intelligence/character-narrative-causality/{character_id}`

### 5.2 Rate Limiting & Caching
- Classified under `EXPENSIVE_READ` tier.
- Integrated with `CacheService` using granular cache keys (`event_narrative:{event_id}:d{max_depth}` and `character_narrative_causality:{character_id}:d{max_depth}`).

---

## 6. Verification Results
- **Unit Tests**: 2/2 passed.
- **Integration Tests**: 7/7 passed.
- **Full Regression Suite**: 396 passed, 0 failed, 0 skipped in 25.23s.
- **Security & Firewall**: Verified across $N-1, N, N+1$.
- **Series Isolation**: Cross-series lookups strictly rejected with 404.
