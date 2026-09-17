# Phase 5.0: Counterfactual & What-If Architecture and Safety Model

## 1. Executive Directive & Safety Contract

**A Counterfactual (What-If) result must NEVER mutate canonical `WorldState` or be represented as canonical story fact.**

The platform enforces absolute memory and persistence isolation between the authoritative canonical timeline and user-initiated hypothetical scenarios.

---

## 2. Counterfactual Isolation Architecture

```mermaid
flowchart TD
    subgraph Canonical_Storage ["Authoritative PostgreSQL Storage (Immutable)"]
        A[(Canonical Events & Entities)] --> B[WorldStateBuilder]
        B --> C[Canonical WorldState at Chapter N]
    end

    subgraph Memory_Sandbox ["Isolated In-Memory Sandbox (Ephemeral)"]
        C -- "1. Deep Clone" --> D[Sandbox Base WorldState]
        E[User What-If Assumption] --> F[Counterfactual Engine]
        D --> F
        F -- "2. Apply Modification" --> G[Altered Initial State]
        H[Canonical Event Stream (Filtered)] --> I[Scenario Replay Runner]
        G --> I
        I -- "3. Re-apply Forward Events" --> J[Hypothetical WorldState at Chapter N]
    end

    subgraph Divergence_Analysis ["Divergence & Explainability"]
        C --> K[WorldStateComparator]
        J --> K
        K --> L[Counterfactual Scenario Result]
    end

    style Canonical_Storage fill:#1e293b,stroke:#0ea5e9,stroke-width:2px
    style Memory_Sandbox fill:#0f172a,stroke:#f59e0b,stroke-width:2px,stroke-dasharray: 5 5
    style Divergence_Analysis fill:#1e1b4b,stroke:#8b5cf6,stroke-width:2px
```

---

## 3. Counterfactual Domain Model

### 3.1 Counterfactual Assumption (`CounterfactualAssumption`)
```python
class AssumptionType(StrEnum):
    PREVENT_EVENT = "PREVENT_EVENT"  # "What if Event X never happened?"
    ALTER_OUTCOME = "ALTER_OUTCOME"  # "What if Character Y survived Event X?"
    INJECT_EVENT = "INJECT_EVENT"  # "What if Skill Z was unlocked early?"


@dataclass(frozen=True)
class CounterfactualAssumption:
    target_event_id: str | None
    target_chapter: int
    assumption_type: AssumptionType
    modification_payload: dict
    justification: str
```

### 3.2 Counterfactual Scenario (`CounterfactualScenario`)
```python
@dataclass(frozen=True)
class CounterfactualScenario:
    scenario_id: str  # Unique UUID or hash
    series_id: str
    base_chapter: int
    reader_chapter: int
    assumption: CounterfactualAssumption
    is_hypothetical: bool = True  # IMMUTABLE MARKER: Always True
    confidence_score: float = 0.85
    invalidated_events: list[str] = field(default_factory=list)
    state_divergence: TemporalComparison = None
    narrative_summary: str = ""
```

---

## 4. Counterfactual Replay Algorithm

```text
Given: series_id, reader_chapter, assumption

1. Validate: assumption.target_chapter <= reader_chapter.
   (Reject if assumption relies on future events > reader_chapter).
2. Fetch canonical WorldState at assumption.target_chapter - 1 as BaseState.
3. Deep-clone BaseState into SandboxState (in memory only).
4. Apply the Assumption modification to SandboxState:
   - If PREVENT_EVENT: Skip target_event.
   - If ALTER_OUTCOME: Invert state delta (e.g. mark character.alive = True instead of False).
5. Fetch subsequent canonical events for chapters in [assumption.target_chapter, reader_chapter].
6. Replay forward using EventApplier:
   a. Check each subsequent event for precondition validity against SandboxState.
   b. If an event's preconditions are broken by the assumption (e.g., dead character acting),
      mark event as INVALIDATED in this branch and omit its application.
   c. If valid, apply event to SandboxState.
7. Run WorldStateComparator.compare(CanonicalState(reader_chapter), SandboxState).
8. Package into CounterfactualScenario with is_hypothetical=True.
9. Return result. Zero database writes.
```

---

## 5. Security & Isolation Guarantees

1. **Read-Only Database Access**: The Counterfactual Use Case does not possess write privileges or write repositories. It only consumes read queries.
2. **Deterministic Hash Identity**: A scenario's identity is computed deterministically:
   $$\text{ScenarioID} = \text{SHA256}(\text{series\_id} + \text{reader\_chapter} + \text{assumption\_type} + \text{canonical\_version})$$
3. **Explicit Hypothetical Stamping**: Every API response, DTO, and log emitted from this engine carries `is_hypothetical: true` to prevent UI confusion.
