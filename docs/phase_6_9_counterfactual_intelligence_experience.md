# Phase 6.9 — Counterfactual / What-If Intelligence Experience Documentation

## 1. Architecture Overview

The **Counterfactual / What-If Intelligence Experience** exposes deterministic simulation and counterfactual analysis to readers at route:

```text
/series/:seriesId/what-if?chapter=N
```

This workspace enables readers to construct hypothetical scenarios anchored at their authoritative reader horizon ($readerChapter = N$), execute counterfactual sandbox models, and visually inspect hypothetical divergence alongside canonical baselines.

```
+-----------------------------------------------------------------------------------+
| What-If Header (Canonical Scope Ch. N | Non-Authoritative Warning | Horizon Stepper)|
+-----------------------------------------------------------------------------------+
| Canonical Context Baseline (Anchor Chapter N | Zero DB Persistence | Ephemeral)   |
+-----------------------------------------------------------------------------------+
|  Left Column (5 cols)                    |  Right Column (7 cols)                 |
|  - Intervention Builder                  |  - Counterfactual Execution State      |
|    * Target Entity Selection             |  - Comparative WorldState Metrics      |
|    * Assumption Type (ALTER, PREVENT...) |    * Status Diffs                      |
|    * Chapter Input (Bounded <= N)        |    * Power Diffs                       |
|    * Proposed Outcome & Justification    |    * Relationship Diffs                |
|  - Scenario Summary Card                 |    * Skills Unlocked                   |
|    * Side-by-Side Transition View        |  - Impacted Entities List              |
|    * CANONICAL vs HYPOTHETICAL           |    * Strikethrough vs New Value        |
|    * Branch Fingerprint ID               |    * NOT CANON Warning Badges          |
|                                          |    * Inspector Probe (Zero N+1)        |
+-----------------------------------------------------------------------------------+
| Counterfactual Safety & Sandbox Provenance Panel                                  |
| - Canonical Horizon Limit                                                         |
| - Non-Persistence & Cache Isolation Guarantee                                     |
| - Temporal Firewall Barrier (N-1 / N / N+1)                                       |
+-----------------------------------------------------------------------------------+
```

---

## 2. Temporal Guarantees & Firewall Invariants

### 1. Reader Horizon Anchoring ($readerChapter = N$)
- No hypothetical intervention can be configured beyond $readerChapter$.
- Targets for intervention (characters and events) are populated strictly from the canonical read models bounded by $readerChapter$.
- Events with `chapter_number > readerChapter` are filtered out before reaching user selection.

### 2. Backward Navigation Defense ($N \to N-1$)
- When the reader steps backward from Chapter $N$ to Chapter $N-1$, any active scenario targeting a chapter greater than $N-1$ is automatically and purely derived as `null`.
- Stale future hypothetical impacts disappear immediately without risk of information leakage.

### 3. Forward Navigation ($N \to N+1$)
- Stepping forward exposes only newly verified canonical events and entities as valid intervention targets.
- Hypothetical results remain isolated and non-authoritative.

---

## 3. Safety & Sandbox Invariants

1. **Zero Canonical Persistence:**
   - Hypothetical simulations exist strictly in ephemeral memory and transient read-query state.
   - Zero PostgreSQL mutations, zero insertions into canonical tables, and zero updates to `events` or `world_state`.

2. **Cache Isolation:**
   - Hypothetical query keys are cleanly namespaced under `['intelligence', 'temporal-comparison', seriesId, fromChapter, toChapter, readerChapter]`.
   - Canonical caches (`timelineFeed`, `storyOverview`, `storyGraph`) are never polluted or invalidated by hypothetical runs.

3. **Explicit Semantic Marking:**
   - Every simulated delta, metric tile, and list row explicitly carries:
     - `is_hypothetical: true`
     - `NOT CANON` / `SIMULATED CONSEQUENCES` badges
     - Amber and violet warning accents to differentiate from canonical green/blue status.

---

## 4. Zero N+1 Protection

- **Discovery Layer:** Leverages existing cached `useTimelineFeed` and `useStoryGraph` hooks.
- **Initial Page Load:** 0 entity profile requests.
- **Scenario Simulation:** Dispatches exactly 1 targeted `useTemporalComparison` query.
- **Inspector Deep Dive:** Entity inspection occurs only on explicit user click ("Inspect ↗"), fetching no preemptive full profiles.

---

## 5. Regression & Verification Results

All 5 regression gates pass with 0 errors:

1. **Frontend Tests (`vitest`):** 24 test files, 115 passed (0 failed).
2. **Frontend Linter (`oxlint`):** 0 errors.
3. **TypeScript Compilation (`tsc -b`):** 0 errors.
4. **Vite Production Build (`vite build`):** 0 errors (production bundle generated).
5. **Backend Unit Tests (`pytest`):** 220 passed (0 failed).
