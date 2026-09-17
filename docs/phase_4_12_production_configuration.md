# Phase 4.12: Authoritative Production Configuration Specification

## 1. Overview

This document specifies the complete, authoritative production configuration for the Timeline Power Visualizer backend. It serves as the single reference for operators, SREs, and deployment engineers.

---

## 2. Environment Variables Specification

### 2.1 Mandatory Production Variables (Fail-Fast)

| Variable | Type | Constraints / Rules | Description |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | `string` | Must be `production` | Enforces all production security policies. |
| `DEBUG` | `boolean` | Must be `false` | Fails startup if `true` in production. |
| `SECRET_KEY` | `string` | Length $\ge 32$ chars, no `dev-insecure` | Token/signature secret. Must be cryptographically generated. |
| `DATABASE_URL` | `string` | Starts with `postgresql://` or `postgresql+psycopg://`; no `timeline_password` | Authoritative PostgreSQL 18 connection string. |
| `CORS_ALLOWED_ORIGINS`| `string` | Comma-separated domains; no `*`; no `localhost` | Allowed web frontend origin domains (HTTPS only). |
| `ALLOWED_HOSTS` | `string` | Comma-separated hostnames; no `*` | Host header validation to prevent DNS rebinding. |
| `TRUSTED_PROXIES` | `string` | Comma-separated IP addresses | Direct socket peers authorized to supply `X-Forwarded-For`. |

---

### 2.2 Optional Variables & Safe Defaults

| Variable | Default | Recommended Production | Description |
| :--- | :--- | :--- | :--- |
| `API_TITLE` | `Timeline Power Visualizer API` | Default | API OpenAPI documentation title. |
| `API_HOST` | `0.0.0.0` | `0.0.0.0` | Server bind host. |
| `API_PORT` | `8000` | `8000` | Server bind port. |
| `CORS_ALLOW_CREDENTIALS`| `true` | `true` | Enable cookie / credential exchange for allowed origins. |
| `MAX_REQUEST_BODY_BYTES`| `1048576` (1 MB) | `1048576` | Upper bound for incoming request body sizes. |
| `DB_POOL_SIZE` | `10` | `10` | SQLAlchemy baseline connection pool size. |
| `DB_MAX_OVERFLOW` | `20` | `10` – `20` | SQLAlchemy burst overflow connection count. |
| `DB_POOL_TIMEOUT_SECONDS`| `30` | `30` | Connection checkout timeout. |
| `DB_POOL_RECYCLE_SECONDS`| `1800` | `1800` (30 min) | Connection recycling interval. |
| `DB_POOL_PRE_PING` | `true` | `true` | Ping on checkout to discard dead connections. |
| `LOG_LEVEL` | `INFO` | `INFO` or `WARNING` | Log severity threshold. Structured JSON emitted. |
| `CACHE_ENABLED` | `true` | `true` | In-process bounded memory cache. |
| `CACHE_MAX_ENTRIES` | `5000` | `5000` | Maximum LRU cache entries. |
| `CACHE_MAX_ENTRY_BYTES` | `524288` (512 KB) | `524288` | Maximum byte size per cached payload. |
| `CACHE_MAX_MEMORY_BYTES`| `67108864` (64 MB) | `67108864` | Process-wide cache memory ceiling. |
| `CACHE_DEFAULT_TTL_SECONDS`| `3600` | `3600` (1 hr) | Cache entry time-to-live. |
| `WORKER_COUNT` | `1` | `1` | Process worker count (enforces in-process safety). |
| `RATE_LIMIT_ENABLED` | `true` | `true` | In-process sliding-window rate limiter. |
| `RATE_LIMIT_DEFAULT_LIMIT` | `120` | `120` req/min | Standard read tier limit. |
| `RATE_LIMIT_DEFAULT_BURST` | `30` | `30` | Standard read tier burst capacity. |
| `RATE_LIMIT_EXPENSIVE_LIMIT`| `30` | `30` req/min | WorldState / Search / Analytics limit. |
| `RATE_LIMIT_EXPENSIVE_BURST`| `10` | `10` | Expensive read tier burst capacity. |
| `RATE_LIMIT_MUTATING_LIMIT` | `60` | `60` req/min | Mutation / Publishing limit. |
| `RATE_LIMIT_MUTATING_BURST` | `15` | `15` | Mutation tier burst capacity. |

---

## 3. Forbidden Values in Production

The following configurations cause the application to terminate immediately during startup:
- `DEBUG=true`
- `SECRET_KEY` containing `dev-insecure` or length $< 32$
- `CORS_ALLOWED_ORIGINS` containing `*` or `localhost` / `127.0.0.1`
- `ALLOWED_HOSTS` containing `*`
- `DATABASE_URL` containing `timeline_password` or pointing to a non-PostgreSQL scheme
- `WORKER_COUNT > 1` when `CACHE_ENABLED=true` or `RATE_LIMIT_ENABLED=true`
- Any negative integer for pool sizes, limits, or timeouts

---

## 4. Operational & Deployment Architecture

1. **Process Sizing**: Deploy a single Uvicorn process per container instance (`WORKER_COUNT=1`).
2. **Reverse Proxy / TLS**: Terminate TLS at the edge / reverse proxy (Nginx, ALB, Caddy). Forward `X-Forwarded-For` and `X-Forwarded-Proto` over trusted loopback or VPC networks.
3. **Database Migrations**: Run migrations (`alembic upgrade head`) strictly out-of-band prior to starting the application containers.
4. **Probes**:
   - Liveness Probe: `GET /health` (lightweight, zero DB load, rate-limit exempt).
   - Readiness Probe: `GET /ready` (verifies PostgreSQL connection via `SELECT 1`).
