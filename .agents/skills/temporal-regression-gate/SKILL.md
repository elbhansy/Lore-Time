---
name: temporal-regression-gate
description: >-
  Execution skill for running and validating the complete 5 regression gates
  (Frontend Vitest, Backend Pytest, TypeScript compile, Oxlint, and Vite Build).
  Use this skill whenever verifying stability before closing any phase or reviewing code changes.
---

# Temporal Regression Gate Skill

Use this procedure to verify that zero regressions exist across all architectural layers.

## Execution Steps

### Step 1: Run Frontend Tests
Execute:
```powershell
npx vitest run
```
(Within `apps/web/`)
Expected: All test suites pass (80+ tests passed, 0 failed).

### Step 2: Run TypeScript Typecheck & Production Bundle
Execute:
```powershell
npm run build
```
(Within `apps/web/`)
Expected: `tsc -b` and `vite build` complete with 0 errors.

### Step 3: Run Frontend Linter
Execute:
```powershell
npm run lint
```
(Within `apps/web/`)
Expected: `oxlint` finishes with 0 errors.

### Step 4: Run Backend Python Test Suite
Execute:
```powershell
pytest -q
```
(From workspace root)
Expected: 400+ unit and integration tests pass with 0 failed.

## Verification Report Criteria
Before declaring any task completed:
- [ ] Frontend Tests: 0 failed
- [ ] Backend Tests: 0 failed
- [ ] TypeScript: 0 errors
- [ ] Lint: 0 errors
- [ ] Build: 0 errors
