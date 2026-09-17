# Temporal Story Intelligence — Agent Instructions

This repository contains the full-stack **Temporal Story Intelligence** platform (FastAPI + React 19 + PostgreSQL).

## Autonomous Agent Mandates

When acting as an agent in this project:

1. **Strictly Guard Temporal Boundaries**:
   - The reader horizon is determined by `readerChapter`. Never reveal or query future story intelligence.
   - Respect backend temporal read models as the single source of truth.

2. **No N+1 Query Patterns**:
   - When developing list, graph, or matrix views, never fetch individual entity profiles. Use projection read models (`GenericGraphReadModel`, `StoryOverviewReadModel`, etc.).

3. **Verify All 5 Regression Gates Before Completion**:
   - Frontend tests: `npx vitest run`
   - Production build: `npm run build`
   - Linting: `npm run lint`
   - Backend tests: `pytest -q`
   All must pass with 0 errors.

4. **Preserve Closed Phases**:
   - Phases 5.0 through 6.6 are verified and stable. Do not redesign or refactor completed phase components.
