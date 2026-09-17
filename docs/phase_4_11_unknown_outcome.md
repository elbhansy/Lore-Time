# Phase 4.11: Unknown Transaction Outcome Scenario Verification

## Executive Overview
In distributed client-server systems, the **Unknown Transaction Outcome** is one of the most critical edge cases:
1. A client initiates a mutating request (e.g. publishing an approved fact/event).
2. The database processes the transaction, writes all canonical models, and successfully commits to disk.
3. Before the HTTP response reaches the client, a network partition, client-side socket timeout, or connection sever occurs.
4. The client is left in total uncertainty: did the write succeed, or was it rolled back?
5. The client (or an automated retry worker) retries the identical logical operation.

This document details how the **Timeline Power Visualizer** architecture safely prevents duplicate logical effects under this scenario without introducing a secondary or incompatible idempotency layer.

---

## Architectural Mechanisms Enforcing Single Logical Effect

The platform utilizes a defense-in-depth model built directly into PostgreSQL ACID transactions and the domain publishing pipeline:

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API as API / Worker
    participant Repo as SQLAlchemyPublicationRepository
    participant DB as PostgreSQL 18 (SSoT)

    Note over Client,DB: Attempt 1: Transaction Commits, but Client Times Out
    Client->>API: POST /publish (review_item_id=X)
    API->>Repo: execute(ReviewItem)
    Repo->>DB: BEGIN TRANSACTION
    Repo->>DB: SELECT FOR UPDATE (review_item_id=X) [Status=APPROVED]
    Repo->>DB: INSERT INTO events (...) ON CONFLICT (publication_fingerprint) DO NOTHING
    Repo->>DB: INSERT INTO publication_records (...)
    Repo->>DB: UPDATE review_items SET status='PUBLISHED'
    Repo->>DB: COMMIT (Success)
    Note over API,Client: Network Drop / Socket Timeout (Client receives no response)

    Note over Client,DB: Attempt 2: Client Retries Unknown Outcome
    Client->>API: POST /publish (review_item_id=X) [RETRY]
    API->>Repo: execute(ReviewItem)
    Repo->>DB: BEGIN TRANSACTION
    Repo->>DB: SELECT FOR UPDATE (review_item_id=X)
    DB-->>Repo: Status = PUBLISHED
    Note over Repo: Concurrency/Retry Interceptor: detected status is already PUBLISHED
    Repo->>Repo: Early Return (Idempotent No-Op)
    Repo->>DB: ROLLBACK / END (No mutations)
    API-->>Client: HTTP 200 OK (Status=PUBLISHED)
```

### 1. In-Transaction Row Locking & Status Check (`lock_review_item`)
Inside the atomic transaction block of `PublishReviewItemUseCase`, the system locks the `review_items` row using `SELECT ... FOR UPDATE`:
```python
locked = self.repo.lock_review_item(review_item.id)
if locked is not None:
    current_status = getattr(locked, "status", None)
    if current_status in (ReviewStatus.PUBLISHED.value, ReviewStatus.PUBLISHED):
        review_item.status = ReviewStatus.PUBLISHED
        return  # Early exit: no duplicate inserts attempted
```
If Attempt 1 successfully committed, Attempt 2 immediately reads the committed `status = 'PUBLISHED'`, sets the domain object status to `PUBLISHED`, and exits cleanly without attempting secondary inserts.

### 2. Publication Fingerprint Deduplication (`save_event`)
Even in scenarios where the retry is synthesized from raw extracted data before review queue hydration, canonical events are protected by a deterministic SHA-256 fingerprint:
$$\text{Fingerprint} = \text{SHA-256}(\text{series\_id}, \text{chapter\_id}, \text{event\_type}, \text{subject\_id}, \text{target\_id}, \text{sorted\_payload})$$
The database table `events` enforces uniqueness:
```sql
CONSTRAINT uq_event_publication_fingerprint UNIQUE (publication_fingerprint)
```
And the insertion uses `ON CONFLICT (publication_fingerprint) DO NOTHING`:
```python
stmt = (
    insert(EventModel)
    .values(...)
    .on_conflict_do_nothing(index_elements=["publication_fingerprint"])
)
self.session.execute(stmt)
```

### 3. Canonical Entity & Relationship Uniqueness
- **Entities**: Upserted via `INSERT INTO canonical_entities ... ON CONFLICT (series_id, id) DO NOTHING`.
- **Relationships**: Graph projections compute deterministic keys based on the event and source/target identities. Full graph rebuilder guarantees set-level deduplication.

---

## Test Verification

### Test Case
- **Test**: `test_unknown_transaction_outcome_retry_produces_single_logical_effect`
- **File**: `tests/integration/database/recovery/test_database_failure_recovery.py`
- **Environment**: Live PostgreSQL 18 database (`postgresql+psycopg://timeline_user:***@localhost:5432/timeline_db`).

### Scenario Steps Executed
1. Seeded a valid series, chapter, and review item in `APPROVED` status.
2. **Attempt 1**: Executed `PublishReviewItemUseCase.execute()` in `session_attempt1`. The transaction committed all canonical rows to PostgreSQL. Simulated network drop by closing the session without notifying the client.
3. **Attempt 2 (Retry)**: Client instantiated a fresh `ReviewItem` domain object from intent and submitted it via `session_attempt2`.
4. Executed `PublishReviewItemUseCase.execute()` in `session_attempt2`.
5. Inspected the live PostgreSQL tables:

### Asserted Invariants

| Assertion Target | Expected Count | Actual Count | Status |
| :--- | :--- | :--- | :--- |
| Canonical Events (`events`) | Exactly 1 | 1 | **PASSED** |
| Publication Records (`publication_records`) | Exactly 1 | 1 | **PASSED** |
| Review Item Status (`review_items.status`) | Strictly `'PUBLISHED'` | `'PUBLISHED'` | **PASSED** |
| Canonical Entities (`canonical_entities`) | Exactly 1 per ID | 1 per ID | **PASSED** |
| Canonical Relationships (`canonical_relationships`) | Exactly 1 | 1 | **PASSED** |

---

## Conclusion
Under the unknown transaction outcome scenario where a commit succeeded but the caller suffered a connection fault:
- **Zero duplicate canonical events** are created.
- **Zero duplicate publication records** are created.
- **Zero orphan or duplicate relationships** are created.
- The platform guarantees **exactly one logical effect** across arbitrary client retries.
