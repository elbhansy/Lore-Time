---
name: temporal-story-intelligence
description: >-
  Expert intelligence skill for the Temporal Story Intelligence platform.
  Use this skill when implementing new frontend features, querying read models,
  enforcing the Temporal Firewall, verifying zero N+1 queries, validating series isolation,
  or running backend/frontend regression gates.
---

# Temporal Story Intelligence Runbook

This skill guides the agent in developing, querying, and verifying features on the **Temporal Story Intelligence** platform.

## 1. Architectural Architecture & Core Contracts

### Reader Horizon & Temporal Firewall
* The current reader horizon is exclusively driven by `TemporalContext.readerChapter`.
* **Golden Rule**: Information with `chapter > readerChapter` must NEVER be exposed or inferred.
* When selecting an entity (character/event) and moving the chapter backwards: if that entity is not yet known at the new chapter, selection must be automatically cleared to avoid leaking stale future context.

### Read Model Endpoints & Models
All intelligence is consumed via read models in `apps/api/app/schemas/read_models.py` and `apps/web/src/api/contracts/read-models.ts`:
1. `StoryOverviewReadModel` (`GET /api/v1/series/{series_id}/intelligence/overview?chapter={reader_chapter}`)
2. `TimelineReadModel` (`GET /api/v1/series/{series_id}/intelligence/timeline?chapter={reader_chapter}&from={from}&to={to}`)
3. `CharacterReadModel` (`GET /api/v1/series/{series_id}/intelligence/characters/{character_id}?chapter={reader_chapter}`)
4. `GenericGraphReadModel` (`GET /api/v1/series/{series_id}/intelligence/graph?chapter={reader_chapter}&graph_type={relationship|causal}`)
   - Nodes: `UniversalGraphNode` (`id`, `label`, `node_type`, `chapter`, `metadata`)
   - Edges: `UniversalGraphEdge` (`edge_id`, `source_id`, `target_id`, `edge_type`, `label`, `weight`, `evidence_summary`)

---

## 2. Preventing N+1 Queries

* **Strict Rule**: Rendering collection surfaces (Character Explorer, Relationship Graph) must make **0** profile requests.
* **Lightweight Representation**: Use nodes/edges directly from `GenericGraphReadModel` or summary counts in `StoryOverviewReadModel`.
* **Deep Profile**: Loaded only when navigating directly to `/series/:seriesId/characters/:characterId?chapter=N`.

---

## 3. Database & Infrastructure Reference

* **User**: `timeline_user`
* **Password**: `timeline_password`
* **Database**: `timeline_db`
* **Port**: `5432` (Docker local)
* **Production Timeouts**:
  - `statement_timeout = '15s'`
  - `idle_in_transaction_session_timeout = '30s'`
* **Backup & Restore**:
  - Backup: `pg_dump -h localhost -U timeline_user -d timeline_db -Fc -f <path>.dump`
  - Restore: `pg_restore -h localhost -U timeline_user -d timeline_db --clean --if-exists -v <path>.dump`

---

## 4. Verification & Regression Workflow

Whenever making modifications, execute the 5 regression gates:

```bash
# 1. Frontend Tests
cd apps/web && npx vitest run

# 2. Frontend Lint
cd apps/web && npm run lint

# 3. TypeScript Type-checking & Build
cd apps/web && npm run build

# 4. Backend Tests
pytest -q
```

All gates must report **0 errors, 0 failed**.
