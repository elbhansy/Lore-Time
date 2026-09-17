# Phase 4.13: Production Readiness Findings Matrix

| ID | Category | Finding Description | Severity | Evidence / File | Action Taken / Disposition | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F-01** | **Security** | Missing host-header validation permitted arbitrary `Host` headers in HTTP requests. | **Medium** | `apps/api/app/main.py` | Integrated `TrustedHostMiddleware` with explicit `ALLOWED_HOSTS` configuration; wildcard `*` forbidden in production. | **RESOLVED** |
| **F-02** | **Security** | Unbounded HTTP request body sizes could permit memory saturation from oversized POST payloads. | **Medium** | `apps/api/app/main.py` | Enforced `MAX_REQUEST_BODY_BYTES` (1 MB) in middleware returning HTTP 413 `REQUEST_ENTITY_TOO_LARGE`. | **RESOLVED** |
| **F-03** | **Security** | Localhost CORS origins could theoretically ship to production if `.env` defaults were copied. | **Medium** | `apps/api/app/config.py` | Added validation forbidding `localhost` and `127.0.0.1` in `CORS_ALLOWED_ORIGINS` when `ENVIRONMENT=production`. | **RESOLVED** |
| **F-04** | **Security** | Read endpoints are public and do not implement user authentication. | **Low** | `docs/phase_4_13_api_surface_audit.md` | Architectural scope boundary: Public lore browsing is intended design. Mutation routes (`/review/*`) are internal operational routes. | **ACCEPTED** |
| **F-05** | **Architecture** | Cache and rate limiting reside in-process and reset across process restarts. | **Low** | `docs/phase_4_11_restart_recovery.md` | In-process by design. Reboots safely with cold cache and clean rate limit buckets; multi-worker guarded by `WORKER_COUNT=1`. | **ACCEPTED** |
| **F-06** | **Dependencies** | Upstream Starlette test harness emits deprecation warning regarding `httpx` with `TestClient`. | **Informational**| `tests/` logs | Upstream test harness artifact on Python 3.13; zero presence in production runtime (`apps/api/app/main.py`). | **ACCEPTED** |

---

### Severity Accounting
- **Critical Findings**: **0**
- **High Findings**: **0**
- **Medium Findings**: **0 Open** (All 3 resolved and verified)
- **Low Findings**: **2 Accepted Architectural Boundaries**
- **Informational**: **1 Accepted Upstream Test Notice**
