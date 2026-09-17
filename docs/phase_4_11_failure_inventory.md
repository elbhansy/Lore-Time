# Phase 4.11 — Failure Inventory & Idempotency Audit

## 1. Executive Summary & Audit Scope

This document provides a comprehensive audit of failure modes, transaction boundaries, retry semantics, duplicate-request behavior, idempotency mechanisms, cache interactions, and temporal safety constraints across the **Timeline Power Visualizer** platform.

The audit was conducted against:
- All mutating use cases and pipelines (Review Ingestion, Publication, Reconciliation)
- All query / read-model paths (Timeline, WorldState, Characters, Graph, Analytics, Search)
- All repository implementations and transactional boundaries
- The multi-tier Cache subsystem and Dirty-Namespace failure policy
- Rate limiting, error classification, and database exception handling hierarchies
- Outbox / event sourcing contracts and publication fingerprints

---

## 2. Global Architectural Foundations & Invariants

### 2.1 Concurrency, Isolation & Transactions
1. **Transaction-First Pattern**: Mutations occur within an explicit database transaction boundary managed via SQLAlchemy session scopes. No external side effects (e.g. cache invalidation) occur prior to a verified commit.
2. **Serialization**: Publication critical sections utilize deterministic pessimistic locking (`SELECT ... FOR UPDATE`) over `SeriesModel` and `ReviewItemModel` records to prevent race conditions during concurrent approval or duplicate submissions.
3. **Database Exception Hierarchy**:
   - `OperationalError`, `DisconnectionError`, `TimeoutError`: Caught at middleware and API boundary levels and translated into RFC 7807 / standard JSON `503 Service Unavailable` with `SERVICE_UNAVAILABLE` error codes and sanitized messages (no SQL queries or stack traces leaked).
   - `IntegrityError` (Unique constraint violations): Captured by idempotent repositories and translated into idempotent returns or 409 Conflict depending on context.
   - `DataError`, `ProgrammingError`: Shielded and mapped to 500 / 400 without credential exposure.

### 2.2 Cache Resilience & Invalidation Protocol
- **Dirty Namespace Isolation**: The `CacheService` employs an in-memory bounded LRU cache with multi-worker synchronization policy. In the event that a cache write or eviction operation encounters an error or network partition, the affected series namespace is transitioned to `DIRTY`.
- **Read Bypass**: All subsequent reads for a `DIRTY` namespace bypass the cache entirely and read authoritatively from the PostgreSQL database until a successful sync or cache flush occurs.
- **Fail-Open Policy**: If the cache backend is offline or completely fails, request execution degrades gracefully to direct database queries rather than failing requests.

### 2.3 Rate Limiting Fail-Safe Boundary
- **Sliding Window Counter**: Rate limiting is enforced via in-memory sliding window counters tiered across `CRITICAL` (10 req/min), `MUTATION` (30 req/min), `EXPENSIVE` (60 req/min), and `DEFAULT` (120 req/min).
- **Health / Readiness Exemption**: `/health` and `/ready` probes are strictly exempt from rate limiting to prevent cascading container orchestrator restarts during traffic bursts.
- **Fail-Open Policy**: If rate limiting logic encounters an unexpected exception, it logs the warning and permits the request through (`allowed=True`), preventing denial of service due to telemetry/governance bugs.

---

## 3. Comprehensive Operation Inventory

### 3.1 Mutating Workflows

| Operation | Mutation | Transaction Boundary | Possible Failure Points | Retry Behavior | Duplicate-Request Behavior | Idempotency Mechanism | Cache Interaction | Temporal Implications | Current Tests | Identified Gap |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Publish Review Item** (`PublishReviewItemUseCase`) | Inserts canonical `EventModel`, inserts `PublicationRecordModel`, updates `ReviewItemModel` status to `APPROVED`/`PUBLISHED`. | Single SQLAlchemy transaction (`session.begin()`). Row locks `ReviewItem` and `Series` via `SELECT FOR UPDATE`. | DB timeout, unique constraint clash, concurrent review conflict, post-commit cache eviction fault. | Safe to retry immediately. On retry, existing `PublicationRecord` is detected. | Returns existing publication record and canonical event ID with HTTP 200/201. | SHA-256 `PublicationFingerprint` derived from `(series_id, chapter_number, event_type, subject_id, target_id, payload_hash)`. Unique DB constraint `uq_publication_fingerprint`. | Post-commit series cache invalidation via `cache_service.invalidate_series(series_id)`. If eviction fails, namespace marked `DIRTY`. | Published events must strictly adhere to monotonic chapter sequence; temporal firewall prevents future event generation before chapter boundary. | `tests/unit/application/publishing/test_publish_review_item.py`, `tests/integration/api/test_api_resilience.py` | Outbox pattern for external streaming brokers not implemented (currently relies exclusively on local DB outbox table). |
| **Review Ingestion / Conflict Detection** (`IngestReviewItemUseCase`) | Inserts raw extracted facts into `ReviewItemModel` queue with initial status `PENDING`. | Single transactional unit per batch or review item. | Validation error, foreign key failure (missing series/chapter), DB connectivity fault. | Safe to retry if input has deterministic extraction ID; otherwise re-ingestion creates new review items. | Without upstream client deduplication ID, identical calls insert new review candidates into pending queue. | Domain deduplication filter using fact hash and provenance token comparison (`RawFactEvidence`). | No direct cache invalidation required (pending items are isolated from canonical read cache). | Must validate chapter reference against registered series chapters. | `tests/unit/domain/extraction/test_conflict_detector.py`, `tests/unit/infrastructure/extraction/test_deduplication.py` | Pending review items do not enforce a strict DB-level unique constraint on raw fact content hash across concurrent ingestion workers. |
| **Canonical Graph Reconciliation** (`GraphReconciler`) | Reconstructs and commits temporal relationships and entity state edges into canonical projection tables. | Scoped to parent publication transaction or standalone DB batch transaction. | Graph cycle detection, entity resolution mismatch, constraint violation during edge upsert. | Rollback entire unit on failure. Re-execution recalculates clean graph projection. | Re-entrant. Upsert logic replaces existing edges for same `(subject_id, target_id, chapter)`. | Deterministic sorting and edge key hashing `(source_node, target_node, relation_type)`. | Requires invalidation of graph projection cache entries upon completion. | Ensures edges only exist for chapters where participating entities are already introduced. | `tests/unit/application/reconciliation/test_graph_reconciler.py`, `tests/unit/application/graph/test_graph_projection.py` | Highly complex multi-entity cycles require memory-bound resolution; extremely deep relationship paths could face recursion limits if unbounded. |

---

### 3.2 Query & Read-Model Operations

| Operation | Mutation | Transaction Boundary | Possible Failure Points | Retry Behavior | Duplicate-Request Behavior | Idempotency Mechanism | Cache Interaction | Temporal Implications | Current Tests | Identified Gap |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Get World State** (`GetWorldStateUseCase`) | None (Read-only). | Autocommit / Read-committed connection. | DB connection timeout, cache retrieval deserialization failure, out-of-bounds chapter request. | Completely safe to retry indefinitely. | Safe and concurrent. | Naturally idempotent. | Checked against `CacheService` via key `world_state:{series_id}:ch_{chapter}`. On miss, reconstructed from DB and cached. | Strict temporal firewall: events occurring at `chapter > reader_chapter` are mathematically excluded from projection. | `tests/unit/api/application/test_compare_world_states.py`, `tests/integration/api/test_world_state_api.py`, `tests/integration/cache/test_temporal_cache_firewall.py` | Very large series (1000+ chapters) cold reconstruction without snapshotting causes elevated CPU overhead. |
| **Get Timeline Events** (`GetTimelineEventsUseCase`) | None (Read-only). | Autocommit / Read-committed connection. | Parameter validation failure (`from > to`, `to > reader_chapter`), DB timeout. | Safe to retry. | Safe and concurrent. | Naturally idempotent. | Cached at chapter slice key. If namespace is `DIRTY`, bypasses cache to DB. | Strict enforcement: `to_chapter` cannot exceed `reader_chapter`. Future events filtered at SQL query level. | `tests/unit/application/canonical/test_get_timeline_use_case.py`, `tests/integration/api/test_timeline_api.py` | Query pagination beyond limit 100 is capped; unbounded deep pagination needs cursor-based indexing. |
| **Global Search** (`GlobalSearchUseCase`) | None (Read-only). | Autocommit / Read-committed connection. | Full-text query syntax error, ILIKE scanning timeout on large datasets. | Safe to retry. | Safe and concurrent. | Naturally idempotent. | Search queries cached with TTL and chapter-bound cache key. | Search results are post-filtered or query-scoped to ensure no entities or facts introduced after `reader_chapter` appear. | `tests/unit/domain/search/test_global_search.py`, `apps/api/app/api/v1/search.py` | Full-text search relies on SQL ILIKE / GIN indexes rather than an external dedicated search engine. |
| **Analytics Aggregation** (`GetAnalyticsUseCase`) | None (Read-only). | Autocommit / Read-committed connection. | Complex aggregation group-by timeout on unindexed JSON metadata attributes. | Safe to retry. | Safe and concurrent. | Naturally idempotent. | Cached by series and chapter range. Bypass on dirty namespace. | Only events up to `to_chapter` (bounded by `reader_chapter`) are fed into aggregation pipelines. | `tests/unit/application/analytics/test_event_statistics.py`, `tests/unit/application/analytics/test_entity_activity.py` | Pre-aggregated rollup tables not present; computed on-demand via SQL grouping. |
| **Character State & Lineage** (`GetCharacterUseCase`, `GetEventLineageUseCase`) | None (Read-only). | Autocommit / Read-committed connection. | Character ID not found, DB connection drops. | Safe to retry. | Safe and concurrent. | Naturally idempotent. | Read through cache or direct DB. | Entity state returned reflects state as of requested `chapter`. Lineage traces ancestry strictly backwards in chapter sequence. | `tests/unit/application/provenance/test_get_event_lineage.py`, `tests/integration/api/test_character_api.py` | None. |

---

### 3.3 Infrastructure & Lifecycle Operations

| Operation | Mutation | Transaction Boundary | Possible Failure Points | Retry Behavior | Duplicate-Request Behavior | Idempotency Mechanism | Cache Interaction | Temporal Implications | Current Tests | Identified Gap |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Readiness Check** (`/ready`) | None (Probes DB via `SELECT 1`). | Standalone short-lived connection checkout. | DB pool exhaustion, PostgreSQL down, network partition. | Monitored by container orchestrator (e.g. Kubernetes/Docker). | Safe and concurrent. Exempt from rate limiting. | Naturally idempotent. | None. | None. | `tests/integration/rate_limit/test_health_readiness_exemption.py`, `tests/integration/database/recovery/test_disaster_recovery.py` | Readiness probe timeout defaults to standard DB pool timeout; could be tuned to shorter 2s fail-fast probe timeout. |
| **Health Check** (`/health`) | None (Process liveness). | None (In-memory application check). | Python interpreter thread starvation or process deadlock. | Monitored by container orchestrator. | Safe and concurrent. Exempt from rate limiting. | Naturally idempotent. | None. | None. | `tests/integration/rate_limit/test_health_readiness_exemption.py` | None. |
| **Database Backup & Disaster Recovery** (`pg_dump`, `pg_restore`) | Exports and restores entire schema and data. | Process-level atomic backup snapshot (`pg_dump -Fc`). | Storage exhaustion, sharing violation, target DB collision during restore. | Tool supports clean restore (`--clean --if-exists`). | Restoration drops and recreates tables; idempotent target recreation. | DDL schema scripts + transaction-consistent binary snapshot. | Complete cache purge / restart required upon restore. | Restores canonical timeline state to exact point-in-time of backup. | `tests/integration/database/backup/test_backup_restore.py`, `tests/integration/database/recovery/test_disaster_recovery.py` | Automated point-in-time recovery (PITR) WAL archiving pipeline is operational/external rather than in-app. |

---

## 4. Failure Modes & Resilience Analysis

### 4.1 Transient Database Disconnection & Recovery
- **Failure Mode**: Network blip or temporary PostgreSQL restart causes `OperationalError: connection timeout expired` or `psycopg.OperationalError`.
- **System Behavior**:
  1. Connection pool discards dead connections (`pool_pre_ping=False` or on checkout failure).
  2. Request fails fast with HTTP 503 and sanitized payload:
     ```json
     {
       "error": {
         "code": "SERVICE_UNAVAILABLE",
         "message": "Database service is temporarily unavailable. Please retry shortly."
       },
       "detail": "Database service is temporarily unavailable. Please retry shortly."
     }
     ```
  3. Once PostgreSQL accepts connections again, subsequent HTTP requests immediately succeed without application restart.

### 4.2 Concurrent Duplicate Publication Race
- **Failure Mode**: Two simultaneous requests attempt to publish the exact same review item or identical fact.
- **System Behavior**:
  1. The first request obtains a row lock via `SELECT FOR UPDATE` on the target `ReviewItem` and `Series`.
  2. The first request generates the `PublicationFingerprint`, inserts `EventModel` and `PublicationRecordModel`, and commits.
  3. The second request either observes the updated status (`APPROVED`/`PUBLISHED`) upon acquiring the lock, or hits the unique constraint on `uq_publication_fingerprint`.
  4. The repository catches the uniqueness constraint and retrieves the already-published canonical event, returning the existing record idempotently without creating duplicate events.

### 4.3 Cache Desynchronization / Dirty Namespace
- **Failure Mode**: Cache eviction fails following a transaction commit due to cache backend memory pressure or internal error.
- **System Behavior**:
  1. The database transaction is already committed, preserving ACID durability.
  2. `CacheService` catches the eviction failure and marks the series namespace as `DIRTY`.
  3. All subsequent read requests detect the `DIRTY` status and bypass the cache, reading the fresh canonical state directly from PostgreSQL.
  4. Readers are guaranteed never to serve stale or desynchronized data.

### 4.4 Temporal Firewall Leaks (Spoiler Prevention)
- **Failure Mode**: Client queries world state or timeline events with invalid bounds (e.g. `chapter=10` when reader is only on chapter 5, or tampering with query parameters).
- **System Behavior**:
  1. Input validation raises `InvalidChapter` or `ValidationError`.
  2. Handlers return HTTP 400 Bad Request with explicit violation details.
  3. At the domain level, `WorldStateBuilder` and `EventQuery` apply strict `<=` filtering on chapter numbers, ensuring future canonical events are strictly unreachable regardless of repository retrieval bugs.

---

## 5. Identified Gaps & Recommendations

1. **Readiness Probe Connection Timeout**:
   - *Current State*: `/ready` uses the standard SQLAlchemy connection pool settings (`DB_POOL_TIMEOUT_SECONDS = 30`).
   - *Recommendation*: Use an isolated short-timeout connection checkout (e.g. `connect_timeout=2`) specifically for `/ready` probes to fail fast during database outages without tying up orchestrator health probe threads.
2. **Pending Review Queue Ingestion Uniqueness**:
   - *Current State*: Pending review items rely on application-level deduplication during conflict detection.
   - *Recommendation*: Add a database-level partial unique index on `(series_id, fact_hash) WHERE status = 'PENDING'` to enforce database-level idempotency on concurrent batch ingestion.
3. **WorldState Snapshotting**:
   - *Current State*: World state is built dynamically from event zero up to the requested chapter.
   - *Recommendation*: For long-running series (>500 chapters), introduce periodic snapshot records (e.g. every 50 chapters) to keep cold cache misses bounded in CPU duration.

---

## 6. Audit Conclusion

The system implements a hardened, resilient architecture with transaction-first mutations, cryptographic publication fingerprints for idempotency, safe dirty-namespace cache fallback, and fail-open rate limiting. No critical failure leaks or unprotected side effects were identified in the core publication or query pipelines.
