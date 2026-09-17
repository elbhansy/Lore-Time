# Temporal Story Intelligence — Workspace Rules

You are working within the **Temporal Story Intelligence** repository.

## Core Architectural Invariants

1. **Temporal Firewall Authority**:
   - The authoritative boundary is `TemporalContext.readerChapter`.
   - Never expose information beyond `readerChapter` (e.g., characters introduced later, future turning points, subsequent relationships, or later causal links).
   - Backend filtering is the primary truth; frontend local filtering is only a defense-in-depth measure.
   - Do not invent split temporal horizons (no `graphChapter`, `profileChapter`, etc.).

2. **Series Isolation**:
   - Every API request, cache key, and database query must be strictly scoped by `seriesId`.
   - React Query cache keys must always include `[..., seriesId, chapter, ...]`.

3. **No Invented Intelligence in Frontend**:
   - Data flow is strictly: `Backend DB -> Read Model -> API Client -> React Query -> Feature Components -> Visualization`.
   - The frontend must never derive semantic relationship meanings, invent fake fields, or run speculative graph intelligence.

4. **Zero N+1 Profile Requests**:
   - Rendering list views or graph topologies (e.g., 50–100 characters) must consume read models directly and execute **0** individual character profile queries.
   - Deep character profiles are only fetched upon explicit user navigation to `/series/:seriesId/characters/:characterId?chapter=N`.

5. **Closed Backend & Frontend Phases**:
   - Phases 5.0 through 6.6 are CLOSED and stable.
   - Do not modify, refactor, or reopen completed phases without concrete regression blockers.

6. **Regression Verification Gates**:
   Before concluding any phase or major change, verify:
   - Frontend tests: `npx vitest run` -> 0 failed
   - Backend tests: `pytest -q` -> 0 failed
   - TypeScript: `tsc -b` -> 0 errors
   - Linting: `oxlint` or `npm run lint` -> 0 errors
   - Production build: `npm run build` -> 0 errors
