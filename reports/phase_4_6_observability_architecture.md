# Phase 4.6 — Observability Architecture Audit

## 1. Overview & Scope

This report documents the architectural audit of logging and observability mechanisms across the **Temporal Story Intelligence Web Application** backend. The system spans FastAPI HTTP routing, application services, domain models, and PostgreSQL persistence with SQLAlchemy.

---

## 2. Current Logging Architecture

### 2.1 Logging Configuration & Setup
- **Module**: `apps/api/app/core/logging.py`
- **Root Logger**: Configured via standard `logging.StreamHandler(sys.stdout)` with `SensitiveDataFilter`.
- **Formatter**: `%(asctime)s [%(levelname)s] [%(name)s] %(message)s` (`datefmt="%Y-%m-%d %H:%M:%S"`).
- **Log Level**: Governed by `Settings.LOG_LEVEL` (defaults to `INFO`, configurable via `.env`).
- **Sanitization Filter**: `SensitiveDataFilter` masks passwords inside database connection strings (`:****@`).

### 2.2 Logger Hierarchy
- `timeline.api`: Used in `main.py` and `apps/api/app/core/logging.py`.
- `timeline.publisher`: Target namespace for canonical publishing and ingestion pipelines.
- `timeline.db`: Target namespace for database operations and transaction failures.
- `timeline.security`: Target namespace for security events and boundary violations.

---

## 3. Request Lifecycle & Context Propagation

### 3.1 Existing Flow
1. Incoming HTTP Request arrives at FastAPI.
2. `add_security_headers` middleware executes.
3. FastAPI router unpacks parameters and resolves dependencies (`get_db`, Use Cases).
4. Use case executes domain logic.
5. Response returned or exception caught by exception handlers.

### 3.2 Missing Lifecycle & Correlation Points (Gaps Identified)
- **Request ID Correlation**: No request ID or correlation ID is currently extracted, generated, or bound to execution context. Log records cannot be correlated across a single request's lifecycle.
- **Request Lifecycle Logging**: No deterministic `request.started`, `request.completed`, or `request.failed` events with durations.
- **Structured JSON Logging**: The current log formatter produces free-form plain text strings rather than machine-parsable structured JSON logs.
- **Contextual Fields**: Application and database logs lack structured fields like `request_id`, `series_id`, `duration_ms`, and `operation`.

---

## 4. Exception & Failure Lifecycle

### 4.1 Exception Handlers (`apps/api/app/main.py`)
- Standardized handlers catch domain exceptions (`ResourceNotFound`, `InvalidChapter`, `ValidationError`, `ConflictError`, `DatabaseUnavailable`, `DatabaseTimeout`, `TransactionFailure`, `SQLAlchemyError`, `Exception`).
- Handlers log selectively (e.g. `logger.error("Database operational error: %s", exc)`).
- **Gaps**:
  - Handlers do not attach `request_id` to log entries or error responses (via headers).
  - Validation errors (`RequestValidationError`) and `ResourceNotFound` are handled without structured logging, causing blind spots for 4xx anomalies.
  - Log records do not log structured JSON metadata.

---

## 5. Database & Transaction Observability

### 5.1 Repository & Session Layer
- `apps/api/app/dependencies/database.py`: Manages SQLAlchemy sessions with automatic rollback on exception.
- `SQLAlchemyPublicationRepository`: Manages row locks (`SELECT FOR UPDATE`) and atomic publishing transactions (`execute_in_transaction`).
- **Gaps**:
  - Publishing lifecycle (`review.publish.started`, `completed`, `conflict`, `rollback`) is not emitting semantic observability events.
  - Slow operations or transaction rollbacks do not record duration or structured operation context.

---

## 6. Security & Temporal Privacy Safeguards

### 6.1 Requirements
- **No Secret Leakage**: Database URLs, tokens, passwords, cookies, and authorization headers must be stripped from all logs.
- **Log Injection Protection**: External user inputs (query params, search strings, request IDs) must be sanitized against newline injection (`\r`, `\n`) and terminal control sequences.
- **Absolute Temporal Privacy (Spoiler Firewall)**: Log events must NEVER record future entities, future event contents, or future character descriptions when reader chapter bounds are evaluated.

---

## 7. Audit Summary

| Component | Current State | Target Phase 4.6 State |
| :--- | :--- | :--- |
| **Format** | Free-text stream formatter | Dual-mode: Structured JSON (or formatted text in test/dev) with structured extras |
| **Correlation** | None | `X-Request-ID` extraction/generation via contextvars & response header |
| **Request Events** | Missing | Structured `request.started`, `request.completed`, `request.failed` with `duration_ms` |
| **Operation Events** | Ad-hoc / missing | Semantic events (`world_state.build.completed`, `review.publish.completed`, etc.) |
| **Database Events** | Handled in main.py | `database.operation.failed`, `database.transaction.rollback` |
| **Log Injection** | Vulnerable to newlines in user inputs | Newline & control character sanitization in log filter/formatter |
| **Secret Redaction** | Basic URL regex | Extended regex masking passwords, tokens, bearer auth, cookies |
| **Temporal Privacy**| Untested in logs | Dedicated filter and tests preventing chapter > readerChapter leakage in logs |
