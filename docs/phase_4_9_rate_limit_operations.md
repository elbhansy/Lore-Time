# Phase 4.9 — Rate Limiting Operations & Runbook

## 1. Operational Configuration

Rate limiting parameters are managed centrally via `.env` or application configuration:

```env
# Enable or disable rate limiting entirely
RATE_LIMIT_ENABLED=true

# Operational Tiers (Limit req/min, Burst allowance)
RATE_LIMIT_DEFAULT_LIMIT=120
RATE_LIMIT_DEFAULT_BURST=30

RATE_LIMIT_EXPENSIVE_LIMIT=30
RATE_LIMIT_EXPENSIVE_BURST=10

RATE_LIMIT_MUTATING_LIMIT=60
RATE_LIMIT_MUTATING_BURST=15

# Memory and Identity Bounds
RATE_LIMIT_MAX_IDENTITIES=10000        # Max client IPs tracked in RAM
RATE_LIMIT_MAX_HITS_PER_IDENTITY=100    # Hard ceiling on timestamps per identity deque
RATE_LIMIT_WINDOW_SECONDS=60          # 1 minute evaluation window

# Trusted Network Proxies (for secure IP extraction)
TRUSTED_PROXIES=127.0.0.1,::1

# Deployment Enforcement
WORKER_COUNT=1                        # Multi-worker safety enforcement
```

---

## 2. Multi-Worker Deployment Policy

> [!CAUTION]
> **IN-PROCESS RATE LIMITING RESTRICTION:**
> Rate limiting runs in application process memory.
>
> In multi-worker deployments (`WORKER_COUNT > 1`):
> - Each process has an independent memory store.
> - Counters are **not** synchronized across worker processes.
> - Therefore, `RATE_LIMIT_ENABLED=true` is valid **ONLY for single-process deployments (`WORKER_COUNT=1`)**.
>
> If `WORKER_COUNT > 1` is configured with `RATE_LIMIT_ENABLED=true`, the application triggers a configuration violation at startup and either rejects launch or disables the limiter with a high-severity alert.

---

## 3. Trusted Proxy IP Extraction Policy

To prevent attackers from bypassing limits or framing victim IP addresses via spoofed `X-Forwarded-For` headers:
1. The limiter checks the immediate socket peer (`request.client.host`).
2. If the peer is **NOT** in `TRUSTED_PROXIES`, `request.client.host` is used as the client identity. Any `X-Forwarded-For` header is **strictly ignored**.
3. If the peer **IS** in `TRUSTED_PROXIES`, the leftmost client IP from `X-Forwarded-For` is extracted and validated.

---

## 4. HTTP 429 Error Contract

When a client exceeds their allowance:
- **HTTP Status**: `429 Too Many Requests`
- **Header**: `Retry-After: <seconds>` (deterministic integer indicating seconds until capacity resets).
- **Body**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later."
  },
  "detail": "Too many requests. Please try again later."
}
```

---

## 5. Fail-Safe Degradation & Error Throttling

If an unexpected exception occurs inside the rate limiter:
- The system **fails open** (allows the request through) to preserve API availability.
- To prevent log flooding during system degradation, `rate_limit.error` events are **throttled to at most one log entry every 5 seconds**.
