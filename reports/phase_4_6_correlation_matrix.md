# Phase 4.6 — Request Correlation Matrix

## 1. Overview
This matrix traces end-to-end request correlation propagation across all architectural boundaries of the application, from the incoming HTTP request through middleware, routers, application use cases, repositories, database error handlers, and the final client response.

---

## 2. Correlation Lifecycle Propagation

```text
Client Request (optional X-Request-ID)
      ↓
[Middleware] Request Validation & ID Generation (set_current_request_id)
      ↓ (request.started logged)
[Router] FastAPI Endpoint Parameter Unpacking
      ↓
[Use Case] Domain Application Execution (ContextVar accessible)
      ↓
[Repository] SQLAlchemy Data Fetch / Transaction
      ↓
[Failure / Exception Handlers] Centralized Handler extracts get_current_request_id()
      ↓
[Response Headers] X-Request-ID injected into response headers
      ↓ (request.completed / request.failed logged with duration_ms)
Client Response Received
```

---

## 3. Correlation Verification Across Components

| Layer / Component | Correlation Mechanism | Request ID Availability | Log Record Field | Status |
| :--- | :--- | :---: | :---: | :--- |
| **HTTP Request Arrival** | `X-Request-ID` header validated or UUIDv4 generated | Yes | `request_id` in `request.started` | **VERIFIED** |
| **Middleware Context** | `contextvars.ContextVar("request_id_ctx")` | Yes | `request_id` in all child tasks | **VERIFIED** |
| **FastAPI Routers** | Inherited from context | Yes | Available via `get_current_request_id()` | **VERIFIED** |
| **Application Services** | Inherited from context | Yes | Injected in `world_state.build.completed` etc. | **VERIFIED** |
| **Publishing Pipeline** | Inherited from context | Yes | Injected in `review.publish.*` events | **VERIFIED** |
| **Repository Layer** | Inherited from context | Yes | Injected in `database.transaction.*` | **VERIFIED** |
| **Exception Handlers** | Centralized in `apps/api/app/main.py` | Yes | Injected in all 4xx/5xx logs & response headers | **VERIFIED** |
| **HTTP Response Headers** | `response.headers["X-Request-ID"]` | Yes | Accessible to API client & log analyzers | **VERIFIED** |

---

## 4. Edge Cases Tested
1. **Client sends clean UUID**: Preserved, echoed, and used in all logs.
2. **Client sends malformed/injection string (`\r\n`)**: Sanitized, rejected, replaced with fresh UUIDv4.
3. **No client header**: Automatically assigned UUIDv4.
4. **Unhandled server crash (500)**: Handled, request ID attached to error response header and internal error log.
