# Phase 4.10 — Workload Inventory

## 1. Scope

This inventory reviews the repository for operations that could plausibly require asynchronous or durable background execution under the Temporal Story Intelligence platform constraints. The review is based on the current FastAPI + PostgreSQL + SQLAlchemy + domain/application/infrastructure architecture already present in this repository.

## 2. Repository Evidence

The repository contains the following major workload families:

- Canonical review/publication pipeline in `apps/api/app/application/publishing/publish_review_item.py`
- Temporal world-state reconstruction and analytics in `apps/api/app/application/timeline/get_world_state.py`
- Global search and visibility filtering in `apps/api/app/application/search/global_search.py`
- Cache and rate-limit hardening in `apps/api/app/core/cache` and `apps/api/app/core/rate_limit`
- Temporal safety enforcement in `packages/domain/services/world_state_builder.py`
- PostgreSQL publication idempotency in `apps/api/repositories/canonical/sqlalchemy_publication_repository.py`

## 3. Candidate Operations and Classification

| Operation | Current execution model | Estimated duration | CPU / I/O | Transaction behavior | Failure modes | Retry safety | Idempotency requirements | Temporal implications | HTTP timeout problem? | Persistence required? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Review publication | Synchronous application service transaction, repository row lock, canonical event insert, publication record insert, post-commit cache invalidation | Low to medium: usually milliseconds to a few seconds | CPU + DB I/O; bounded, transactional | Explicit DB transaction with commit after canonical write | Validation failure, DB timeout, rollback, duplicate canonical event race | Yes, if retried after a failed transaction; operation is re-entrant under idempotent fingerprint logic | Mandatory. Duplicate publication must not create duplicate canonical event or publication record. | Must remain within current readerChapter / publication rules; no future content leakage | No, it is already bounded and transactional | No durable external job queue required; DB is source of truth |
| WorldState reconstruction | Synchronous read path; optionally cached by `CacheService.get_or_compute` | Medium for large series; low under cache, high on cold miss | CPU-heavy in-memory recomputation, DB fetch I/O | Read-only, no DB mutation; backend uses repository reads and in-memory rebuild | Cache failure or DB read failure; stale/inconsistent cache is handled by validation and invalidation | Safe to retry because it is read-only | Idempotent by definition, no mutating effects | Strict `readerChapter` firewall enforced in `WorldStateBuilder` | The system already caches hot reads and enforces rate limits; not a background job case | No durable job queue required |
| Global search / temporal filtering | Synchronous read path with cached compute | Medium, dependent on result set size and DB size | CPU + DB I/O | Read-only with deterministic post-filtering | Search repo failure, cache invalidation on publication | Read-only retry is safe | No mutating side effects | Must not expose future entities/events; sanitization and chapter bound checking are enforced | Expensive reads are already rate-limited and cached | No durable job queue required |
| Analytics aggregation | Synchronous read path with cache gating | Medium to heavy for large canonical histories | CPU-heavy aggregation + DB reads | Read-only | Cache miss or DB failure | Safe to retry | Read-only, idempotent | Must honor `readerChapter`/temporal visibility | Rate-limited, cache-backed; not a job candidate | No durable job queue required |
| Graph projection / relationship generation | Synchronous and embedded in publication transaction | Low to medium | DB writes + graph reconstruction | Part of canonical publication flow | Transaction rollback on failure | Re-run after rollback is acceptable if idempotent keys are reused | Mandatory to avoid duplicate relations | May not expose future edges before chapter boundaries | Not a request-time timeout issue in current model | No independent queue required |
| Review ingestion / normalization / extraction | Repository and domain logic are currently synchronous and DB-backed | Low to medium depending on input volume | DB + parsing I/O | Usually transactional if persisted | Validation errors, repository failure | Safe to retry only within existing persisted transaction boundaries | Depends on source semantics, but not a durable async generic workload in this repo | Must preserve chapter-bound story semantics | Not significant enough to justify external jobs | No durable job queue required in the current implementation |
| Bulk import / archival / maintenance scripts | Scripted, not part of the live API path | Variable | CPU + filesystem + DB I/O | Usually controlled by script-level transactions | Partial import, connection interruption | Must be idempotent if re-run; script-level logic governs retry | Yes, but these are operational tasks rather than online request work | Can be temporally scoped at script admission | Not a user-facing timeout issue unless manually invoked via API | Persistence is handled by the database and script process itself; not a durable app queue |
| External API calls / third-party integrations | No active external broker/integration infrastructure is visible in the repository | Unknown | Network + latency | No durable transaction boundary currently modeled | Timeout, network fault, partial response | Would need domain-level idempotency if implemented | Not currently present; no workload proof here | No implicit temporal leakage path in current repo | Not currently relevant to this codebase | No evidence of required durable job infrastructure |
| Filesystem operations | No dedicated background job subsystem or durable queue is present | Variable | Local I/O | Usually script-managed, not request-managed | Disk I/O failure | Script-level retry semantics required if present | Not a core API use case in the app | Not tied to temporal visibility | Not a current HTTP timeout requirement | No durable job queue required |

## 4. Long-Running Operation Classification

### 4.1 Operations that are actually expensive but remain synchronous-safe

The repository already contains the mechanisms needed for the actual expensive efforts:

1. `CacheService` with bounded in-process LRU storage and dirty-namespace fallback.
2. `rate_limit` with endpoint tiering and fail-open safety.
3. Publication repository with row locking (`SELECT FOR UPDATE`) and idempotent canonical inserts.
4. Temporal filters and validation at both application/service and domain layers.

These patterns mean the workload is not “missing a queue”; it is “missing a more selective read-optimization strategy,” which the project already addresses through caching and bounds enforcement.

### 4.2 Operations that are not justified as durable background jobs

The following categories do not currently justify background execution in this repo:

- World-state rebuilds are expensive but are already cached and bounded.
- Search results are compute-heavy but remain request-bound and rate-limited.
- Analytics are read-only and deterministic; the app caches them.
- Publication is already transactional and idempotent in the database.
- There is no evidence of a long-running user-facing task whose completion must survive HTTP completion, worker restarts, or multi-process crashes.

## 5. Failure and Recovery Review

The repository already demonstrates the correct operational model:

- publication uses a DB transaction boundary and commit ordering that keeps the database authoritative
- cache invalidation happens after a successful commit, matching the project’s Phase 4.8 contract
- rollback handling is explicit and deterministic
- idempotent canonical publication avoids duplicate events via fingerprint-based checks and ON CONFLICT DO NOTHING

This is materially different from a durable task queue, where the system must persist queue state, worker leasing, retry scheduling, and crash-recovery semantics. The current repository does not show a workload that requires that additional machinery.

## 6. Findings

The workload inventory does not justify a durable background job system for the current application.

The relevant operations are either:

- short-lived transactional flows already handled in PostgreSQL,
- read-heavy operations already optimized through single-process caching and rate limiting,
- or operational/admin tasks that are intentionally out-of-band and not part of the request path.

## 7. Decision Summary

No durable asynchronous job subsystem is required for the present codebase.

The current platform already satisfies the essential production requirements:

- canonical correctness through DB transactions
- idempotent publication via fingerprint checks
- temporal safety through `readerChapter` validation
- bounded read optimization through in-process cache
- abuse protection through rate limits
- failure isolation via transactional commit/rollback and dirty-cache fallback

## 8. Relevant Repo References

- `apps/api/app/application/publishing/publish_review_item.py`
- `apps/api/repositories/canonical/sqlalchemy_publication_repository.py`
- `apps/api/app/application/timeline/get_world_state.py`
- `apps/api/app/application/search/global_search.py`
- `packages/domain/services/world_state_builder.py`
- `apps/api/app/config.py`
- `apps/api/app/main.py`

## 9. Conclusion

Phase 4.10 does not require introducing Celery, Redis, RabbitMQ, or another external broker for this repository as it exists today. The proven workload is already handled by PostgreSQL transactions, idempotent canonical publication, bounded caching, and rate limiting. Any “job” model beyond that would be speculative infrastructure.
