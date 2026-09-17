# Phase 4.12: Production Configuration Inventory

## 1. Overview & Objective

This document inventories the existing configuration architecture across the Timeline Power Visualizer platform. It catalogs all configuration sources, precedence, defaults, production-sensitive settings, safe behaviors, hardcoded assumptions, and areas requiring explicit hardening for production deployment.

---

## 2. Configuration Sources & Precedence

The application derives its configuration from `apps/api/app/config.py` using `pydantic-settings.BaseSettings`.

### Evaluation Order (Pydantic Settings Precedence):
1. **Explicit keyword arguments** passed to `Settings(...)` (highest priority; used in tests).
2. **OS Environment Variables** (`os.environ`).
3. **Dotenv File** (`.env` in current working directory, UTF-8 encoded).
4. **Field Defaults** specified in `Settings` class definitions (lowest priority).

---

## 3. Configuration Inventory Matrix

| Configuration Key | Type | Default Value | Production Sensitivity | Hardening / Validation Status |
| :--- | :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | `Environment` enum | `development` | High | Validates `development`, `test`, `production`. |
| `DEBUG` | `bool` | `False` | Critical | Validated: Fails fast if `True` when `ENVIRONMENT=production`. |
| `SECRET_KEY` | `str` | `dev-insecure-secret-key-change-in-production-32bytes!` | Critical | Validated: Must be $\ge 32$ chars and not contain `dev-insecure` in production. |
| `API_TITLE` | `str` | `Timeline Power Visualizer API` | Low | Safe string default. |
| `API_HOST` | `str` | `0.0.0.0` | Medium | In production, must bind to container / interface. |
| `API_PORT` | `int` | `8000` | Medium | Standard port. |
| `CORS_ALLOWED_ORIGINS` | `list[str]` | `[localhost:5173, 127.0.0.1:5173, localhost:3000, 127.0.0.1:3000]` | Critical | Validated: `*` forbidden in production. Parses comma-separated string or list. |
| `CORS_ALLOW_CREDENTIALS` | `bool` | `True` | High | Pair with explicit origins (cannot be wildcard). |
| `DATABASE_URL` | `str` | `postgresql+psycopg://timeline_user:timeline_password@localhost:5432/timeline_db` | Critical | Validated: Must start with `postgresql` and reject `timeline_password` in production. |
| `DB_POOL_SIZE` | `int` | `10` | High | Validated non-negative. |
| `DB_MAX_OVERFLOW` | `int` | `20` | High | Validated non-negative. |
| `DB_POOL_TIMEOUT_SECONDS`| `int` | `30` | High | Validated non-negative. |
| `DB_POOL_RECYCLE_SECONDS`| `int` | `1800` | High | Validated non-negative. Prevents stale connections. |
| `DB_POOL_PRE_PING` | `bool` | `True` | High | Ensures dead sockets are recycled prior to checkout. |
| `LOG_LEVEL` | `str` | `INFO` | Medium | Validated via logging setup. |
| `CACHE_ENABLED` | `bool` | `True` | High | Bounded in-process cache. |
| `CACHE_MAX_ENTRIES` | `int` | `5000` | High | Ceiling for LRU cache entries. |
| `CACHE_MAX_ENTRY_BYTES` | `int` | `524288` (512 KB) | High | Max size per individual cache entry. |
| `CACHE_MAX_MEMORY_BYTES` | `int` | `67108864` (64 MB) | High | Global in-memory cache ceiling. |
| `CACHE_DEFAULT_TTL_SECONDS`| `int` | `3600` (1 hr) | Medium | Expiration duration. |
| `CACHE_VERSION` | `str` | `v1` | Medium | Key namespace versioning. |
| `WORKER_COUNT` | `int` | `1` | Critical | Multi-worker safety: If $>1$, requires `CACHE_ENABLED=False` and `RATE_LIMIT_ENABLED=False`. |
| `RATE_LIMIT_ENABLED` | `bool` | `True` | Critical | Sliding window rate limiting. |
| `RATE_LIMIT_DEFAULT_LIMIT` | `int` | `120` | High | Standard read rate limit (req/min). |
| `RATE_LIMIT_DEFAULT_BURST` | `int` | `30` | High | Standard read burst. |
| `RATE_LIMIT_EXPENSIVE_LIMIT` | `int` | `30` | High | Expensive read rate limit (req/min). |
| `RATE_LIMIT_EXPENSIVE_BURST` | `int` | `10` | High | Expensive read burst. |
| `RATE_LIMIT_MUTATING_LIMIT` | `int` | `60` | High | Mutating write limit (req/min). |
| `RATE_LIMIT_MUTATING_BURST` | `int` | `15` | High | Mutating write burst. |
| `RATE_LIMIT_MAX_IDENTITIES` | `int` | `10000` | High | Maximum client keys tracked in memory. |
| `RATE_LIMIT_MAX_HITS_PER_IDENTITY` | `int` | `100` | High | Maximum hits stored per client identity. |
| `RATE_LIMIT_WINDOW_SECONDS`| `int` | `60` | High | Rate limit window duration. |
| `TRUSTED_PROXIES` | `list[str]` | `["127.0.0.1", "::1"]` | Critical | `X-Forwarded-For` only trusted if socket client is in this list. |

---

## 4. Hard-Coded Values & Architectural Assumptions

1. **Single-Worker In-Process Constraint**:
   - The application enforces `WORKER_COUNT=1` when in-process cache or rate limiting is enabled.
   - Multi-worker or distributed deployments with external caches/brokers are explicitly forbidden unless distributed storage is introduced.
2. **CORS Development Origins**:
   - Defaults include `http://localhost:5173` and `http://localhost:3000`. In production, these must be overridden by explicit production origins.
3. **Database URL Default**:
   - Default contains sample credentials (`timeline_user:timeline_password`). Production fails fast if this password is present.
4. **Allowed Hosts**:
   - FastAPI handles host routing; Trusted Host middleware should be formally integrated to reject invalid or spoofed `Host` headers in production.
5. **Frontend API URL**:
   - In `apps/web/src/services/api/client.ts`, `BASE_URL` is configured as `/api/v1` (relative path). This correctly leverages reverse proxy or same-origin deployment without hardcoded local ports.

---

## 5. Existing Safe Behaviors

1. **Password Redaction**: `sanitized_database_url` masks passwords as `:****@`. Logging filter `SensitiveDataFilter` scrubs passwords, bearer tokens, API keys, and session cookies from all log records.
2. **Fail-Fast Production Validation**: `model_validator(mode="after")` in `Settings` prevents startup if `DEBUG=True`, if `SECRET_KEY` is default/short, if CORS contains `*`, or if default DB passwords are used.
3. **Rate Limiting Proxy Protection**: `extract_client_identity` ignores `X-Forwarded-For` unless the immediate socket peer is explicitly in `TRUSTED_PROXIES`.
4. **Health vs Readiness Separation**:
   - `/health`: Liveness probe, performs zero database I/O, does not leak credentials, exempt from rate limiting.
   - `/ready`: Readiness probe, executes `SELECT 1` via connection pool, catches exceptions safely without leaking connection strings.

---

## 6. Identified Gaps & Production Hardening Requirements

1. **Trusted Host Validation**: Add explicit `ALLOWED_HOSTS` configuration and middleware to guard against DNS rebinding and host-header injection in production.
2. **Request Body Size Ceiling**: Add explicit maximum body size limit to prevent memory exhaustion attacks from oversized payloads.
3. **Database Statement & Connect Timeouts**: Formally document and expose explicit timeouts for pool checkout and query execution.
4. **CORS Explicit Origin Requirement**: In production, `CORS_ALLOWED_ORIGINS` must not fall back to `localhost` dev origins.
