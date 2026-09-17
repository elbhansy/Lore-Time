# Phase 4.13: Production Readiness Inventory

## 1. Overview & Scope

This inventory serves as the foundational audit document for **Phase 4.13: Production Readiness Gate**. It evaluates every layer of the Temporal Story Intelligence backend and web frontend, cataloging components, boundaries, operational safety properties, and deployment assumptions.

---

## 2. Component Inventory & Audit Matrix

| Subsystem / Layer | Concrete File(s) | Architectural Responsibility | Operational & Production Status |
| :--- | :--- | :--- | :--- |
| **Domain Layer** | `packages/domain/*` | Pure business entities, state models, temporal ordering, and graph structures. Zero ORM, zero FastAPI, zero external dependencies. | **PRODUCTION READY**: Completely framework-agnostic. Strictly enforces temporal visibility invariants. |
| **Application Layer** | `apps/api/app/application/*` | Use case orchestrators (WorldState, Publishing, Analytics, Search, Review). | **PRODUCTION READY**: Manages domain operations with clear dependency inversion. |
| **Database Repositories** | `apps/api/repositories/*` | SQLAlchemy Core/ORM queries, PostgreSQL transaction boundaries, row locking. | **PRODUCTION READY**: Bounded queries, indexed aggregations, `SELECT FOR UPDATE` atomic locks. |
| **Database Schema** | `infrastructure/database/models/*` | PostgreSQL 18 table definitions, foreign keys, unique constraints, and indexes. | **PRODUCTION READY**: Fingerprint uniqueness, cascade deletes where appropriate, indexed foreign keys. |
| **Migrations** | `infrastructure/migrations/*`, `alembic.ini` | Schema evolution management via Alembic. | **PRODUCTION READY**: Clean upgrades/downgrades. Decoupled from application startup. |
| **API Transport** | `apps/api/app/api/v1/*`, `main.py` | FastAPI routing, Pydantic DTO validation, HTTP response contracts. | **PRODUCTION READY**: Standardized error envelopes, no stack traces leaked in production. |
| **Configuration** | `apps/api/app/config.py`, `.env.example` | Centralized Pydantic settings with strict production fail-fast rules. | **PRODUCTION READY**: Rejects `DEBUG=True`, weak secrets, wildcard CORS, and localhost origins in production. |
| **Caching Layer** | `apps/api/app/core/cache/*` | Thread-safe, in-process LRU cache (`BoundedMemoryCache`) with dirty namespace bypass. | **PRODUCTION READY**: Memory bounded to 64 MB. Enforces single-worker deployment (`WORKER_COUNT=1`). |
| **Rate Limiter** | `apps/api/app/core/rate_limit/*` | In-process bounded sliding window counter with tier-based throttling and trusted proxy defense. | **PRODUCTION READY**: RAM bounded (< 5 MB). `/health` and `/ready` exempt. |
| **Observability** | `apps/api/app/core/logging.py` | Structured JSON log formatter with correlation ID (`X-Request-ID`) and sensitive data filter. | **PRODUCTION READY**: Automatically masks DB passwords, tokens, bearer auth, and cookies. |
| **Health Probes** | `apps/api/app/main.py` | `/health` (liveness) and `/ready` (database connectivity probe). | **PRODUCTION READY**: Dependency-isolated liveness; non-leaking readiness. |
| **Frontend App** | `apps/web/src/*` | React / Vite UI communicating via relative `/api/v1` client. | **PRODUCTION READY**: Zero hardcoded server ports or leaked backend secrets. |

---

## 3. Operational Guarantees & Non-Functional Boundaries

1. **Transactional Integrity**: All canonical state changes (`PublishReviewItemUseCase`) execute within explicit atomic database transactions. Partial failures trigger clean rollbacks leaving zero orphaned events.
2. **Deterministic Idempotency**: Publication uniqueness is enforced via SHA-256 fingerprint database constraints (`publication_fingerprint`), preventing duplicate canonical events.
3. **Temporal Spoiler Firewall**: Query limits clamp strictly to `readerChapter`. Entities, relationships, and events $> readerChapter$ are inaccessible across all read and search surfaces.
4. **Multi-Tenant Series Isolation**: Series identifiers are validated at repository and query boundaries, preventing cross-tenant data leakage.
5. **Fail-Fast Configuration**: Any missing or unsafe production setting prevents the process from starting.
