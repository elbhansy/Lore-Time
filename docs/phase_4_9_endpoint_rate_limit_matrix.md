# Phase 4.9 — API Endpoint Rate Limit Matrix

## 1. Classification Methodology

Endpoints in the Temporal Story Intelligence platform are audited and classified into four deterministic operational tiers:

1. **EXEMPT**: Operational and orchestration probes (`/health`, `/ready`). Must never be blocked by the rate limiter to guarantee container and load-balancer liveness/readiness detection.
2. **EXPENSIVE_READ**: Endpoints that perform multi-chapter temporal reconstruction, heavy SQL aggregation, complex graph traversal, entity comparison, or vector search. Allocated conservative rate limits and tight burst limits.
3. **MUTATING**: Write endpoints that propose or publish data, modify review queues, or trigger graph re-projections. Governed by moderate limits to prevent write amplification.
4. **STANDARD_READ**: Read-only endpoints with direct indexed lookups, shallow filtering, or high cacheability. Allocated standard generous allowances.

---

## 2. Endpoint Audit & Rate Limit Allocation

| Route Pattern | Method | Classification | Resource Cost & DB / Cache Characteristics | Configured Limit | Burst Allowance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/health` | `GET` | **EXEMPT** | Liveness probe; process memory only; zero DB or cache interaction. | Unlimited | Unlimited |
| `/ready` | `GET` | **EXEMPT** | Readiness probe; runs `SELECT 1` ping; essential for orchestration. | Unlimited | Unlimited |
| `/api/v1/series/{id}/world-state` | `GET` | **EXPENSIVE_READ** | Reconstructs character & relationship state across past events (37ms DB at 10K scale). Highly cacheable. | 30 req/min | 10 |
| `/api/v1/series/{id}/analytics/overview` | `GET` | **EXPENSIVE_READ** | Computes aggregations across all events (68ms DB at 10K scale). Cacheable. | 30 req/min | 10 |
| `/api/v1/series/{id}/analytics/events` | `GET` | **EXPENSIVE_READ** | Event distribution aggregation across types and sequences. | 30 req/min | 10 |
| `/api/v1/series/{id}/analytics/characters` | `GET` | **EXPENSIVE_READ** | Entity activity metrics across chapter bounds. | 30 req/min | 10 |
| `/api/v1/series/{id}/analytics/relationships`| `GET` | **EXPENSIVE_READ** | Relationship changes and transition metrics. | 30 req/min | 10 |
| `/api/v1/series/{id}/search` | `GET` | **EXPENSIVE_READ** | Full-text candidate query + temporal visibility filtering. | 30 req/min | 10 |
| `/api/v1/series/{id}/characters/{id}/relationship-graph` | `GET` | **EXPENSIVE_READ** | Traverses multi-hop relationship graph up to depth 2. | 30 req/min | 10 |
| `/api/v1/series/{id}/relationships/graph` | `GET` | **EXPENSIVE_READ** | Full relationship topology at chapter $N$. | 30 req/min | 10 |
| `/api/v1/series/{id}/comparison` | `GET` | **EXPENSIVE_READ** | Dual entity state comparison at chapter boundary. | 30 req/min | 10 |
| `/api/v1/series/{id}/impact` | `GET` | **EXPENSIVE_READ** | Ripple effect & downstream event impact analysis. | 30 req/min | 10 |
| `/api/v1/review/*` | `POST` | **MUTATING** | Publication and review state transitions. Post-commit cache invalidation. | 60 req/min | 15 |
| `/api/v1/series/{id}/timeline` | `GET` | **STANDARD_READ** | Sequential event envelopes by chapter range (indexed pushdown). | 120 req/min | 30 |
| `/api/v1/series/{id}/characters` | `GET` | **STANDARD_READ** | Character list / profiles for series. | 120 req/min | 30 |
| `/api/v1/series/{id}/characters/{id}` | `GET` | **STANDARD_READ** | Single character lookup. | 120 req/min | 30 |
| `/api/v1/series/{id}/power-systems/*` | `GET` | **STANDARD_READ** | Power systems, ranks, and progression lookups. | 120 req/min | 30 |
| `/api/v1/series/{id}/factions/*` | `GET` | **STANDARD_READ** | Faction intelligence and membership queries. | 120 req/min | 30 |
| `/api/v1/series/{id}/skills/*` | `GET` | **STANDARD_READ** | Skill intelligence and relations. | 120 req/min | 30 |
| `/api/v1/series/{id}` | `GET` | **STANDARD_READ** | Series metadata. | 120 req/min | 30 |

---

## 3. Tier Classifier Contract

Classification is based on **concrete route pattern + HTTP method** matching rather than arbitrary prefix substring matching, preventing accidental misclassification of newly introduced routes.
