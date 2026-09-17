# Phase 4.5 — Security Threat Model & Attack Surface Analysis

**System Under Evaluation:** Temporal Story Intelligence API & Visualizer  
**Assessment Target:** Security Boundaries, Multi-Tenant Isolation, Temporal Firewall Integrity, Input Sanitization, and Injection Resistance  
**Baseline Status:** Phase 4.1 through 4.4 Verified Complete (162 passed tests)

---

## 1. System Overview & Architecture Diagram

```
                 [ Untrusted API Client / Browser Frontend ]
                                     |
                                     v (HTTP / HTTPS)
                    +--------------------------------+
                    |      FastAPI Gateway Layer     |
                    |  - CORS Hardening Middleware   |
                    |  - Defensive Security Headers  |
                    |  - Global Exception Sanitizer  |
                    +--------------------------------+
                                     |
                (Query Validation / Pydantic Parameter Parsing)
                                     |
                                     v
                    +--------------------------------+
                    |     Application / Domain Core  |
                    |  - Series Existence Validation |
                    |  - readerChapter Clamping      |
                    |  - Temporal Firewall Filter    |
                    |  - State Replay & Projections  |
                    +--------------------------------+
                                     |
                (Parametrized ORM / Dialect Execution)
                                     |
                                     v
                    +--------------------------------+
                    |      PostgreSQL 18 Database    |
                    |  - Tables (Series, Events, etc)|
                    |  - Row-level Locks (FOR UPDATE)|
                    |  - Fingerprint Unique Indexes  |
                    +--------------------------------+
```

---

## 2. Identified Threat Actors & Trust Assumptions

| Threat Actor | Description & Motivation | Capabilities |
| :--- | :--- | :--- |
| **Untrusted Public Reader** | Malicious or curious API client seeking early plot spoilers or unreleased story lore beyond their current chapter. | Can craft arbitrary HTTP GET queries, manipulates query parameters (`chapter`, `to`, `from`, `q`, `depth`), tampers with UUIDs. |
| **Cross-Tenant Adversary** | User/tenant attempting to enumerate, extract, or infer metadata and facts belonging to another series (`series_id` tampering). | Manipulates path variables (`{series_id}`) and request entities from foreign series to bypass multi-series boundaries. |
| **Concurrent Malicious Publisher** | Automated client or script attempting race conditions on unapproved review items, aiming to inject unverified facts into the canonical timeline. | Executes concurrent HTTP requests, triggers parallel publishing workflows with invalid status payloads. |
| **Injection / Fuzzing Scanner** | Automated web vulnerability scanner executing SQL injection, JSONB expression probing, or path traversal vectors. | Injects quotes, SQL syntax (`' OR '1'='1`), control characters, deep nesting, and invalid data types across query parameters. |

---

## 3. Threat Matrix (STRIDE Categorization)

| ID | STRIDE Category | Threat Description | Attack Vector / Scenario | Potential Impact | Severity | Existing Mitigation & Defense | Hardening Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- | :---: |
| **T-01** | **Information Disclosure** | Temporal Future Lore Leakage (Spoiler Firewall Bypass) | Client sets `chapter=N` but supplies `to_chapter=N+k` in timeline, event, or analytics endpoints. | Future plot twists, deceased characters, or unearned ranks exposed to reader prematurely. | **Critical** | `GetTimelineEventsUseCase` strictly clamps `to_chapter = min(to_chapter, reader_chapter)`. `EventQuery` and `CompareWorldStatesUseCase` raise `400 INVALID_CHAPTER`. `GlobalSearchUseCase` and `GetRankProgressionUseCase` evaluate temporal predicates against $chapter \le N$. | **VERIFIED HARDENED** |
| **T-02** | **Elevation of Privilege / Auth Bypass** | Cross-Series Lore Access | Attacker queries Series B using entity IDs or power system IDs belonging to Series A. | Multi-series isolation breach, leaking proprietary universe data across distinct series. | **High** | Repository and use-case checks verify entity ownership (`ps.series_id == series_id`, `char.series_id == series_id`). Foreign IDs yield `404 RESOURCE_NOT_FOUND`. | **VERIFIED HARDENED** |
| **T-03** | **Information Disclosure** | Unfiltered Character / System Enumeration | Reader enumerates all characters via `GET /series/{id}/characters` before characters appear in the story. | Hidden characters or villains introduced in future chapters leaked via static table queries. | **Medium** | Endpoint returns non-revealing state (`exists=False`, `alive=False`, `as_of_chapter=0`). Frontend renders state in context of current reader chapter. | **DOCUMENTED ARCHITECTURAL BEHAVIOR** |
| **T-04** | **Tampering / Elevation of Privilege** | Unapproved Fact Publishing Race Condition | Malicious actor invokes publishing pipeline on `PENDING` or `REJECTED` review items concurrently. | Insertion of illegitimate, hallucinated, or unverified facts into canonical timeline and knowledge graph. | **Critical** | `CanonicalPublisher.prepare_event_data` validates `status == ReviewStatus.APPROVED`, raising `PublicationDomainError` otherwise. `SQLAlchemyPublicationRepository` uses `SELECT FOR UPDATE` and `publication_fingerprint` idempotency index. | **VERIFIED HARDENED** |
| **T-05** | **Tampering / Injection** | SQL Injection via Search or Query Filters | Attacker inputs SQL injection fragments (`' UNION SELECT ...`, `'; DROP TABLE ...`) into `q`, `entity_id`, or `type` parameters. | Unauthorized DB read/write, schema destruction, data exfiltration. | **High** | 100% parametrized SQLAlchemy queries and ORM filters (`ilike`, `filter_by`). Zero string interpolation or raw SQL concatenation on user inputs. | **VERIFIED HARDENED** |
| **T-06** | **Information Disclosure** | System Information Disclosure via Error Traces | Client sends malformed payload or triggers database failure to inspect stack trace and schema details. | Attacker learns internal table structures, column names, server paths, or driver versions. | **High** | Centralized exception handlers catch all `SQLAlchemyError`, `OperationalError`, and unhandled `Exception`, mapping them to generic `SERVICE_UNAVAILABLE` or `INTERNAL_SERVER_ERROR`. Stack traces logged strictly to internal logs. | **VERIFIED HARDENED** |
| **T-07** | **Denial of Service** | Resource Exhaustion via Unbounded Queries | Client requests unbounded pagination (`page_size=1000000`) or deep graph traversal (`depth=999`). | Database CPU/memory saturation, connection pool starvation. | **Medium** | FastAPI query validation enforces strict bounds: `page_size <= 100`, `limit <= 100`, `depth <= 2` or `depth <= 3`. | **VERIFIED HARDENED** |
| **T-08** | **Information Disclosure** | Cross-Origin Data Theft (CORS & Framing) | Malicious third-party web page performs unauthorized cross-origin fetches or embeds app in iframe. | Cross-site data exfiltration, clickjacking attacks. | **Medium** | CORS middleware restricts origins using `CORS_ALLOWED_ORIGINS` (wildcards prohibited in production). Security headers inject `X-Frame-Options: DENY` and `X-Content-Type-Options: nosniff`. | **VERIFIED HARDENED** |
| **T-09** | **Tampering / Configuration** | Insecure Production Secrets & Debug Modes | Deployment with default credentials or `DEBUG=True`. | Interactive debugger execution, trivial database compromise. | **Critical** | Pydantic `model_validator` in `apps/api/app/config.py` halts startup if `DEBUG=True`, `SECRET_KEY` is weak/default, or sample DB password is used in production. | **VERIFIED HARDENED** |

---

## 4. Security Boundary Summary

1. **Authentication Layer:** The system operates without an interactive authentication layer; API endpoints are public read interfaces. Publication operations are internal domain services. (Documented Architectural Characteristic).
2. **Temporal Firewall (Hard Boundary):** `readerChapter` is an absolute temporal security boundary. State is reconstructed strictly from events with $chapter \le readerChapter$. No endpoint leaks future state.
3. **Cross-Series Firewall (Hard Boundary):** Every resource is bounded to its owning `series_id`. Foreign identifiers are rejected with `404 RESOURCE_NOT_FOUND`.
4. **Data Plane Isolation:** All SQL queries are parametrized; untrusted inputs cannot escape lexical context.
