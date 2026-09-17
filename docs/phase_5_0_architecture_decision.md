# Phase 5.0: Architecture Decision & Blueprint

## 1. Context & Business Need

The Temporal Story Intelligence platform has achieved full production readiness across core storage, querying, security, and resiliency (Phases 0–4). The next product evolution (Phase 5) introduces **Advanced Story Intelligence**: transforming the deterministic temporal foundation into high-level analytical capabilities—including narrative arcs, causal chains, counterfactual ("What-If") exploration, and compound narrative discovery.

---

## 2. Core Architectural Decisions

### Decision 1: WorldState Remains the Sole Temporal Source of Truth
- **Resolution**: All intelligence analyses, character arcs, and causal deductions must evaluate against `WorldState` snapshots produced by `WorldStateBuilder`.
- **Constraint**: The Knowledge Graph is an ephemeral projection of `WorldState + Domain Entities` and must **never** become an authoritative source of truth.

### Decision 2: Pure In-Memory Counterfactual Sandbox
- **Resolution**: Counterfactual ("What-If") simulations deep-clone `WorldState` in application memory, apply user assumptions, and replay subsequent events using `EventApplier`.
- **Safety Guarantee**: Counterfactual workflows possess **zero database write privileges**. Every response carries `is_hypothetical: true` to prevent any confusion with canonical lore.

### Decision 3: Four-Tier Intelligence Hierarchy
- **Resolution**: Intelligence is categorized into four distinct layers:
  1. *Canonical Intelligence*: Verified story occurrences in PostgreSQL.
  2. *Analytical Intelligence*: Deterministic mathematical deductions from canonical facts.
  3. *Hypothetical Intelligence*: Speculative counterfactual scenarios.
  4. *Presentation Intelligence*: UI views and aggregated visualizations.

### Decision 4: Absolute Temporal Firewall Preservation
- **Resolution**: All Phase 5 intelligence engines strictly enforce the `readerChapter = N` boundary. Any event, entity, relationship, or rank introduced at $> N$ is invisible and dropped prior to computation.

### Decision 5: Zero Speculative Infrastructure
- **Resolution**: No LLMs, graph databases (Neo4j), background worker queues (Celery/RabbitMQ), or distributed caches (Redis) are introduced. All algorithms are pure Python domain engines executing synchronously against PostgreSQL 18.

---

## 3. Scope Boundaries: What Is Explicitly NOT Being Built

1. **No External LLM / Generative AI Dependency**: Narrative intelligence is computed through formal state delta analysis, event dependency graphs, and rule-based trajectory models, not probabilistic language models.
2. **No Graph Database Migration**: The existing relational projection architecture in PostgreSQL remains completely adequate for chapter-bounded DAG traversals.
3. **No Unbounded Scenario Trees**: Counterfactual branching evaluates a single alternative path per request. We are not building exponential tree search algorithms.
4. **No Direct UI Mutation of Canonical State**: Readers cannot alter canonical database state via What-If sandbox interfaces.

---

## 4. Implementation Phasing Roadmap

- **Phase 5.1**: Core Intelligence Domain Models, Value Objects & Invariants.
- **Phase 5.2**: Character Arc Derivation Engine.
- **Phase 5.3**: Causal Intelligence & DAG Tracing Engine.
- **Phase 5.4**: Narrative Intelligence & Turning Point Engine.
- **Phase 5.5**: Counterfactual Simulation Sandbox.
- **Phase 5.6**: Temporal Scenario Explorer.
- **Phase 5.7**: Advanced Narrative Discovery Engine.
- **Phase 5.8**: Story Intelligence Dashboard Application Layer & API Surface.
- **Phase 5.9**: Frontend Visual Explorers & React Components.
