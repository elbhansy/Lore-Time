# Phase 4.10 — Architecture Decision

## 1. Decision

The architecture decision for this repository is:

- No durable background job infrastructure is required.
- No external queue, broker, or Redis/Celery-style system is justified.
- FastAPI request background tasks are not used as a durable job mechanism.
- PostgreSQL remains the authoritative execution and persistence boundary for all current mutating and canonical operations.

This decision is based on the actual workload inventory and the repository patterns already in place.

## 2. Mandatory Answers

### 2.1 Which operations require background execution?

None of the current product-facing operations in this repository require durable background execution.

The strongest candidates are:

- canonical publication of a review item
- world-state reconstruction and analytics
- global search and graph/relationship projection

All of these remain in the live request path, but they are either:

- database-transaction bounded,
- read-only and cacheable,
- or already covered by deterministic temporal and validation safety checks.

### 2.2 Why is synchronous execution insufficient?

It is not insufficient for the current workload. The repository already implements the relevant safeguards:

- row-level locking for review publication
- idempotent canonical inserts with fingerprint checks and `ON CONFLICT DO NOTHING`
- transaction rollback on failure
- post-commit cache invalidation
- temporal filtering and spoiler-firewall enforcement

There is no evidence in the current codebase that a request times out or fails due to a long-running job that must continue after HTTP completion.

### 2.3 Which operations must remain synchronous?

The following remain synchronous and should remain so unless the product introduces a genuinely long-running, user-triggered workload with a clear durable requirement:

- review publication
- world-state rebuilds
- search queries
- analytics queries
- graph/relationship reconstruction
- publication and canonical event creation

These are all either direct DB reads/writes or bounded in-memory computations that are already constrained by caching and rate limiting.

### 2.4 Which operations require durable persistence?

None of the current request-driven operations require a separate durable job queue.

The real persistent source of truth remains PostgreSQL:

- canonical events
- publication records
- review state
- series and chapter data

The current implementation already persists the canonical side effects in the database, which is the correct place to hold authoritative state.

### 2.5 Which operations can use ordinary async I/O?

This repository does not show a need for high-volume async task execution beyond the normal async HTTP request handling already provided by FastAPI.

Ordinary async I/O is appropriate for:

- database connection handling
- request lifecycle and middleware logic
- general I/O-bound application operations

It is not justified to create a custom durable async worker layer for the current dataset and product flow.

### 2.6 Why are FastAPI request background tasks or in-process tasks not sufficient?

They are not sufficient only if a task must outlive an HTTP request and survive crash/restart. The current repository does not present such a workload.

For the existing platform, the use of request-scoped background tasks would be a speculative pattern because:

- there is no durable requirement for recovery across process restart
- there is no evidence of a queue backlog that survives HTTP completion
- the canonical mutation path already has transaction correctness in PostgreSQL
- the system already uses explicit cache invalidation and dirty fallback strategies instead of queueing side effects outside the DB

Therefore, request background tasks are intentionally not used here.

### 2.7 Why are PostgreSQL-backed jobs sufficient or not sufficient?

For this repository they are sufficient because the actual long-running work is not so long-running that it needs a separate job ledger.

The current system’s job-like behavior is already expressed in PostgreSQL transactions:

- publication executes atomically
- idempotent canonical writes prevent duplication
- the database remains the system of record
- the cache is invalidated after commit, not before

There is no current requirement to extract work into a separate `jobs` table or durable poller loop.

### 2.8 Why is an external broker not justified?

An external broker is not justified because the current repository does not exhibit any of the conditions that normally demand one:

- no long-lived user-facing tasks needing durable after-request execution
- no multi-process worker fan-out requirement
- no queue backlog requiring external scheduling or crash recovery beyond DB transactions
- no evidence of external dependency failure rates that warrant a separate durable queue abstraction
- no requirement for event-driven orchestration across multiple application services

Introducing Redis, RabbitMQ, Kafka, Celery, or a similar system would be speculative infrastructure and would violate the project requirement to avoid “not justified” infrastructure.

## 3. Architectural Conclusion

The current repository is correctly modeled around:

- PostgreSQL as the source of truth
- application-level caching as an optimization layer
- rate limiting as abuse control
- temporal validation as correctness guardrail
- atomic canonical publication as the primary mutating workflow

This is a good fit for the existing workload and does not require a durable background job system.

## 4. Contra-indications

A durable job architecture would only become necessary if the project later adds a workload such as:

- a user-initiated long-running import
- a multi-step external ingestion pipeline with retries and partial completion
- a large asynchronous re-processing batch
- a distributed multi-worker system

None of those are presently evidenced in the codebase.

## 5. Final Decision Statement

This repo does not currently justify a durable background jobs implementation. The repository already satisfies the production needs for correctness, idempotency, temporal visibility, cache invalidation, and failure recovery without introducing a separate job framework.
