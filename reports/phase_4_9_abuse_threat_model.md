# Phase 4.9 — Abuse Threat Model & Mitigation Analysis

## 1. Threat Landscape & Prioritization

The Temporal Story Intelligence backend exposes both public and authenticated interfaces. This threat model prioritizes realistic application-level abuse vectors according to their potential impact on database CPU, memory, and application availability.

---

## 2. Attack Vectors & Defensive Countermeasures

| Attack Vector | Attacker Objective | Mechanism | Severity | Defense & Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **1. Expensive WorldState Flooding** | Database/CPU exhaustion | Sending rapid concurrent requests to `/series/{id}/world-state` with rotating chapter numbers to force constant full-history rebuilds. | **CRITICAL** | Strict **EXPENSIVE_READ** tier (30 req/min, burst 10) + Phase 4.8 in-process cache + chapter boundary validation ($1 \le chapter \le total\_chapters$). |
| **2. Temporal Search Storms** | Database load & memory exhaustion | Executing repeated complex search queries to force heavy vector lookups and Python-level visibility filtering. | **HIGH** | Strict **EXPENSIVE_READ** tier (30 req/min, burst 10) + maximum query text length capped at 100 characters + max page size capped at 100. |
| **3. Analytics Aggregation Flooding** | PostgreSQL CPU saturation | Flooding `/series/{id}/analytics/*` endpoints with wide chapter bounds (`from=1&to=1000`). | **HIGH** | Strict **EXPENSIVE_READ** tier (30 req/min, burst 10) + indexed aggregation queries + cache. |
| **4. High-Cardinality Key Memory Abuse** | Process RAM exhaustion | Forcing the rate limiter to store hundreds of thousands of arbitrary client keys. | **HIGH** | `MAX_IDENTITIES=10000` with strict active TTL cleanup and LRU eviction + `MAX_HITS_PER_IDENTITY=100` ceiling to bound entry memory. |
| **5. X-Forwarded-For Spoofing** | Bypass IP rate limiter | Sending spoofed `X-Forwarded-For: 1.2.3.4` headers from untrusted clients to distribute requests across fake identities or frame victim IPs. | **CRITICAL** | **Trusted Proxy Defense**: The limiter exclusively reads the direct socket `client.host`. `X-Forwarded-For` is inspected ONLY if the immediate connection peer is explicitly listed in `TRUSTED_PROXIES`. |
| **6. Invalid Parameter / 404 Probing** | Server scan & resource consumption | Rapidly firing requests with malformed UUIDs, negative chapters, or nonexistent series IDs. | **MEDIUM** | Invalid requests consume rate limit budget at the middleware layer before business processing, throttling probes with 429. |
| **7. Multi-Worker Drift Exploitation** | Limiter quota multiplication | Exploiting multiple worker processes to obtain $N \times$ quota allowance. | **HIGH** | **Deployment Enforcement**: `WORKER_COUNT=1` required when rate limiting is enabled. Multi-worker configurations fail fast or disable rate limiting with loud alerts. |
| **8. Limiter Exception Log Storm** | Log storage exhaustion / DoS | Triggering deliberate errors in the rate limiter to flood disk/logging with millions of exception stack traces. | **MEDIUM** | **Throttled Limiter Error Logging**: Internal limiter exceptions log at most once per 5 seconds, failing open gracefully. |
| **9. Concurrent Request Bursting** | Race condition / quota bypass | Firing $N$ simultaneous asynchronous requests in the same millisecond to slip past counters. | **HIGH** | **Thread-Safe Atomic Execution**: Limiter uses `threading.RLock()` across sliding window checks and updates. |
| **10. Health / Readiness Denial** | Infrastructure downtime | Flooding `/health` or `/ready` to trigger 429, causing Kubernetes/load balancers to kill or take instances out of rotation. | **CRITICAL** | Complete exemption of `/health` and `/ready` from rate limiting. |
| **11. Cache Hit Budget Bypass** | Resource exhaustion via cache | Bypassing rate limiting by repeatedly hitting cached URLs. | **MEDIUM** | Rate limiting executes as the **very first middleware layer**, before cache lookup. All HTTP traffic consumes budget. |
| **12. Permanent Lockout via Stale Keys** | Legitimate user denial | Never resetting counters due to timestamp drift or broken TTL. | **MEDIUM** | Fixed-window sliding decay ensures client automatically recovers after window seconds expire without manual intervention. |
