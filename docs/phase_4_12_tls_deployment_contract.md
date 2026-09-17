# Phase 4.12: TLS / HTTPS Deployment Contract

## 1. Overview & Architecture Boundary

The Timeline Power Visualizer application is designed to operate behind a secure reverse proxy or API gateway (such as Nginx, Cloudflare, AWS ALB, Caddy, or Envoy).

```mermaid
flowchart LR
    Client([Web Browser / Client]) -- "HTTPS (TLS 1.3)" --> Proxy[TLS Terminating Reverse Proxy / Gateway]
    Proxy -- "HTTP (Private VPC / Localhost Socket)" --> App[Timeline API (Uvicorn / FastAPI)]
```

The application layer **does not implement raw TLS certificate termination internally**. Instead, TLS termination occurs at the reverse proxy or ingress gateway, which forwards sanitized traffic to the FastAPI application over an isolated private network or loopback socket.

---

## 2. Forwarded Headers & Proxy Trust Contract

When TLS is terminated upstream, the reverse proxy must pass the following standard headers to the application:

| Header | Expected Value | Purpose |
| :--- | :--- | :--- |
| `X-Forwarded-For` | `<client_ip>, <proxy_ip_1>` | Client IP identification for rate limiting and audit logs. |
| `X-Forwarded-Proto` | `https` | Informs application of original request scheme. |
| `X-Forwarded-Host` | `api.loretime.com` | Informs application of original requested host. |
| `X-Request-ID` | Safe alphanumeric UUID | Optional upstream request tracing correlation. |

### Strict IP Spoofing Defense Guarantee
In accordance with Phase 4.9 and Phase 4.12 hardening:
- `X-Forwarded-For` is **strictly ignored** unless the direct socket peer (`request.client.host`) is explicitly listed in `TRUSTED_PROXIES`.
- If an untrusted direct peer sends an `X-Forwarded-For` header, the application discards it and attributes the request directly to the connecting peer's IP, preventing client IP spoofing and victim framing.

---

## 3. Production HTTPS Deployment Requirements

1. **Mandatory HTTPS Enforcement**:
   - The upstream proxy MUST redirect all unencrypted HTTP traffic (port 80) to HTTPS (port 443) with HTTP 301 Permanent Redirect.
   - Strict-Transport-Security (HSTS) MUST be added by the reverse proxy:
     ```text
     Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
     ```
2. **Defensive Response Headers**:
   FastAPI automatically attaches standard security headers on all responses (including 429 and error responses):
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
3. **Cookie Security**:
   If session or auth cookies are issued in the future, they must enforce:
   ```text
   Secure; HttpOnly; SameSite=Strict
   ```
4. **CORS Protocol Alignment**:
   In production, all origins listed in `CORS_ALLOWED_ORIGINS` must use the `https://` protocol scheme. Unencrypted `http://` origins are prohibited.
