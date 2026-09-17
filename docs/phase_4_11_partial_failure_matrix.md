# Phase 4.11 - Partial Failure Boundaries Matrix

This document provides a comprehensive audit of all system failure boundaries for core mutation workflows, detailing failure injection mechanisms, atomic transaction guarantees, and deterministic recovery behaviors.

---

## 1. Mutation Workflow Boundaries Architecture

In our system architecture, all state transitions and canonical publications follow strict boundary transitions:

```
[Client Request]
       │
       ▼
[1. BEFORE DB MUTATION] ──(Domain Validation / Pre-Flight Checks)
       │
       ▼
[2. DURING DB MUTATION] ──(In-Flight Multi-Table Writes / Projections)
       │
       ▼
[3. AFTER DB MUTATION (BEFORE COMMIT)] ──(Flush / Pre-Commit Locks / Constraint Verification)
       │
       ▼
[4. AFTER COMMIT] ──(DB Commit Succeeded / Network Severed / Outcome Uncertainty)
       │
       ▼
[5. CACHE INVALIDATION] ──(Post-Commit Cache Purge / Dirty Namespace Marking)
       │
       ▼
[Client Response (200 OK)]
```

---

## 2. Partial Failure Matrix

| Failure Boundary | Injected Failure Scenario | State at Point of Failure | System Reaction | Recovery Mechanism | Resulting Invariant |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. BEFORE DB MUTATION** | Domain validation fails (e.g. invalid status, missing subject ID, malformed payload) | Unchanged original state; no DB transaction opened | Rejects request with `PublicationDomainError` or `ValidationError` | No DB recovery needed; client receives `400` / `422` with clear error details | **Zero mutations initiated**; DB remains pristine |
| **2. DURING DB MUTATION** | Database crash or query syntax/type error mid-stream (e.g. event inserted, but entity/relationship projection fails) | Dirty session with uncommitted rows staged in PostgreSQL buffer | Catch block in `SQLAlchemyPublicationRepository.execute_in_transaction` triggers `session.rollback()` | Full PostgreSQL ACID atomic rollback; session discarded | **Zero partial records**; no orphan events or partial graph edges |
| **3. AFTER DB MUTATION (BEFORE COMMIT)** | DB serialization clash, deadlocks, or socket disconnection right before `commit()` | All rows staged and flushed, transaction pending commit | Commit call raises `OperationalError` or `TransactionFailure`; caught by repository | Automatic explicit `session.rollback()` triggered | **Clean abort**; review item remains in original state (`APPROVED`), ready for clean retry |
| **4. AFTER COMMIT** | Database successfully committed mutation, but client experiences connection timeout or severed network before receiving response | Canonical event and publication records committed to database | Client re-issues identical request with original parameters | Deduplication via row lock (`SELECT ... FOR UPDATE`) and fingerprint (`ON CONFLICT DO NOTHING`) | **Deterministic duplicate detection**; exactly 1 canonical event, 0 side effects, returns successful outcome |
| **5. CACHE INVALIDATION** | Mutation committed to PostgreSQL, but cache invalidation call fails (e.g. cache backend crash or timeout) | PostgreSQL commit finalized; cache may contain stale reader view | Post-commit try/except catches invalidation error; marks series namespace as `DIRTY` | Next read detects `is_dirty(series_id) == True`, completely bypasses cache, and queries PostgreSQL directly | **Correctness-first guarantee**; DB transaction is never rolled back for cache errors; no stale reads |

---

## 3. Boundary-by-Boundary Recovery Verification

### Boundary 1: Before DB Mutation
- **Verification Test**: `test_boundary_before_db_mutation_validation_failure`
- **Behavior**: An attempt to publish a review item that is not in `APPROVED` status (e.g. `PENDING`) raises `PublicationDomainError`.
- **Guarantee**: No database transaction is started, no row locks are acquired, and no canonical events or publication records are generated.

### Boundary 2: During DB Mutation
- **Verification Test**: `test_boundary_during_db_mutation_failure_rolls_back_atomically`
- **Behavior**: An exception is injected after `EventModel` and `CanonicalEntityModel` insertion, but during `create_relationship`.
- **Guarantee**: The PostgreSQL transaction rolls back atomically. Zero events, zero entities, and zero relationships remain. The `ReviewItemModel` status remains `APPROVED`.

### Boundary 3: After DB Mutation (Before Commit)
- **Verification Test**: `test_boundary_after_db_mutation_before_commit_rolls_back_atomically`
- **Behavior**: All staging and flushing succeed, but `session.commit()` fails due to a simulated serialization conflict or network drop.
- **Guarantee**: The repository catches the error, triggers `session.rollback()`, and raises an exception. No partial canonical state persists.

### Boundary 4: After Commit (Unknown Outcome Scenario)
- **Verification Test**: `test_boundary_after_commit_network_failure_and_retry`
- **Behavior**: The initial transaction commits to the database, but the client experiences a dropped connection and retries the exact same operation.
- **Guarantee**: The retry safely inspects the committed row state and publication fingerprint. Exactly **1** canonical event and **1** publication record exist. The operation completes deterministically.

### Boundary 5: Cache Invalidation
- **Verification Test**: `test_boundary_cache_invalidation_failure_marks_dirty_and_bypasses`
- **Behavior**: The database transaction commits successfully, but the subsequent cache invalidation call raises an exception.
- **Guarantee**: The committed database transaction is **not** rolled back (Correctness-First). The namespace is marked `DIRTY`. All subsequent read requests detect the dirty flag and bypass the cache to compute fresh results directly from PostgreSQL.

---

## 4. Test Suite Execution & Acceptance

The partial failure boundaries are fully covered in:
- `tests/integration/database/test_partial_failure_boundaries.py`
- `tests/integration/database/test_hardened_publication_recovery.py`
- `tests/integration/database/recovery/test_database_failure_recovery.py`

All tests run against live PostgreSQL with zero mocks for core database behavior:
```text
tests/integration/database/test_partial_failure_boundaries.py ..... [100%]
5 passed in 0.66s
```
