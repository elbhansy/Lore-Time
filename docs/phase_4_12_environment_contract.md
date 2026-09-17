# Phase 4.12: Environment Separation Contract

## 1. Overview & Purpose

This contract establishes strict, deterministic environment boundaries for the Timeline Power Visualizer platform. It defines three distinct operating modes:
- `development`
- `test`
- `production`

**Primary Guarantee**: A production instance **cannot accidentally run with development behaviors, defaults, or security exemptions**. Any invalid or unsafe production configuration triggers an immediate fail-fast termination during application bootstrap before serving any requests.

---

## 2. Environment Matrix & Rules

| Setting | `development` | `test` | `production` | Fail-Fast Enforcement |
| :--- | :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | `test` | `production` | Must be an exact match of the enum. |
| `DEBUG` | `True` or `False` | `True` or `False` | **Strictly `False`** | Fails startup if `DEBUG=True` in production. |
| `SECRET_KEY` | Dev default allowed | Test key allowed | **Mandatory Secure Key** | Must be $\ge 32$ chars, non-empty, and cannot contain `dev-insecure`. |
| `DATABASE_URL` | Local dev database | Test database | **PostgreSQL Connection** | Fails if non-PostgreSQL or contains sample password `timeline_password`. |
| `CORS_ALLOWED_ORIGINS` | Localhost origins allowed | Localhost/mock origins | **Explicit Domains Only** | Fails if `*` is present or if default localhost origins remain unconfigured. |
| `ALLOWED_HOSTS` | `["*"]` or localhost | `["*"]` or test host | **Explicit Hostnames** | Must be explicitly enumerated (e.g. `api.loretime.com`). |
| `TRUSTED_PROXIES` | `["127.0.0.1", "::1"]` | `["127.0.0.1", "::1"]` | **Explicit Reverse Proxy IPs** | Must reflect VPC gateway / edge proxy IP addresses. |
| `LOG_LEVEL` | `DEBUG`, `INFO` | `INFO`, `WARNING` | `INFO`, `WARNING`, `ERROR` | Structured JSON output emitted across all environments. |
| `CACHE_ENABLED` | `True` or `False` | `True` or `False` | `True` (or `False` if scaled) | In-process bounded cache; requires `WORKER_COUNT=1`. |
| `RATE_LIMIT_ENABLED` | `True` or `False` | `True` or `False` | **`True`** | In-process sliding window; requires `WORKER_COUNT=1`. |
| `WORKER_COUNT` | `1` | `1` | `1` | Multi-worker safety: If $>1$, in-process cache & rate limiter must be disabled. |

---

## 3. Production Fail-Fast Rules

During application bootstrap (`apps/api/app/config.py`), when `ENVIRONMENT=production`, the configuration validator strictly enforces:

1. **DEBUG Lockout**:
   ```text
   DEBUG == True => ValueError("Security Violation: DEBUG cannot be True in production environment")
   ```
2. **Secret Key Cryptographic Strength**:
   ```text
   len(SECRET_KEY) < 32 or "dev-insecure" in SECRET_KEY => ValueError("Security Violation: Production requires a secure, non-default SECRET_KEY of at least 32 characters")
   ```
3. **No Wildcard CORS**:
   ```text
   "*" in CORS_ALLOWED_ORIGINS => ValueError("Security Violation: Wildcard '*' CORS origin is strictly prohibited in production environment")
   ```
4. **No Localhost CORS in Production**:
   ```text
   Any origin in CORS_ALLOWED_ORIGINS matching localhost/127.0.0.1 => ValueError("Security Violation: Localhost origins are prohibited in production CORS_ALLOWED_ORIGINS")
   ```
5. **No Sample Credentials in Database URL**:
   ```text
   "timeline_password" in DATABASE_URL => ValueError("Security Violation: Default sample database password detected in production DATABASE_URL")
   ```
6. **PostgreSQL Protocol Required**:
   ```text
   not DATABASE_URL.startswith("postgresql") => ValueError("Production requires a valid PostgreSQL database URL")
   ```
7. **Single-Worker In-Process Constraint**:
   ```text
   WORKER_COUNT > 1 and (CACHE_ENABLED or RATE_LIMIT_ENABLED) => ValueError("Multi-Worker Violation: ... requires WORKER_COUNT=1")
   ```

---

## 4. Environment Transition Verification

To deploy to production, operators must supply production-specific values via environment variables:

```bash
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY="c4ca4238a0b923820dcc509a6f75849b2830f8983c411"
export DATABASE_URL="postgresql+psycopg://app_prod_user:StrongRandomPass2026!@prod-db.internal:5432/timeline_prod"
export CORS_ALLOWED_ORIGINS="https://loretime.app,https://api.loretime.app"
export ALLOWED_HOSTS="api.loretime.app"
export TRUSTED_PROXIES="10.0.0.1,10.0.0.2"
export WORKER_COUNT=1
```

If ANY of the above are omitted, misconfigured, or set to development defaults, the API process terminates immediately with an informative error message and nonzero exit code.
