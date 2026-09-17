import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)
from sqlalchemy.exc import (
    TimeoutError as SATimeoutError,
)

from apps.api.app.api.v1.router import api_router
from apps.api.app.application.exceptions import (
    ConflictError,
    DatabaseTimeout,
    DatabaseUnavailable,
    InvalidChapter,
    ResourceNotFound,
    TransactionFailure,
)
from apps.api.app.application.exceptions import (
    ValidationError as AppValidationError,
)
from apps.api.app.config import get_settings
from apps.api.app.core.logging import (
    get_current_request_id,
    set_current_request_id,
    setup_logging,
)
from apps.api.app.core.rate_limit import (
    EndpointTier,
    build_rate_limit_key,
    classify_endpoint,
    extract_client_identity,
    get_rate_limit_service,
)

logger = logging.getLogger("timeline.api")

# Initialize environment-driven settings & logging
settings = get_settings()
setup_logging()

app = FastAPI(
    title=settings.API_TITLE,
    debug=settings.DEBUG,
)

# Apply hardened CORS middleware from configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply TrustedHostMiddleware if allowed hosts are constrained
if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS != ["*"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


SAFE_REQUEST_ID_REGEX = re.compile(r"^[A-Za-z0-9\-_]{1,64}$")


@app.middleware("http")
async def request_correlation_and_lifecycle_middleware(request: Request, call_next):
    """Correlates requests with an X-Request-ID, establishes contextvars,

    and logs deterministic request.started and request.completed events with duration_ms.
    """
    client_request_id = request.headers.get("X-Request-ID")
    if client_request_id and SAFE_REQUEST_ID_REGEX.match(client_request_id):
        req_id = client_request_id
    else:
        req_id = str(uuid.uuid4())

    token = set_current_request_id(req_id)
    start_time = time.perf_counter()

    # Reject request if Content-Length exceeds MAX_REQUEST_BODY_BYTES
    content_length = request.headers.get("Content-Length")
    if content_length:
        try:
            if int(content_length) > settings.MAX_REQUEST_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "REQUEST_ENTITY_TOO_LARGE",
                            "message": f"Request body exceeds maximum allowed limit of {settings.MAX_REQUEST_BODY_BYTES} bytes",
                        },
                        "detail": f"Request body exceeds maximum allowed limit of {settings.MAX_REQUEST_BODY_BYTES} bytes",
                    },
                    headers={"X-Request-ID": req_id},
                )
        except ValueError:
            pass

    # Log request.started (without raw bodies or auth headers)
    logger.info(
        "Request started: %s %s",
        request.method,
        request.url.path,
        extra={
            "event": "request.started",
            "request_id": req_id,
            "operation": f"{request.method} {request.url.path}",
        },
    )

    # --- Phase 4.9 Rate Limiting & Abuse Protection ---
    tier = classify_endpoint(request.url.path, request.method)
    if tier != EndpointTier.EXEMPT:
        rate_limiter = get_rate_limit_service()
        if rate_limiter.is_enabled:
            client_ip = extract_client_identity(request, settings.TRUSTED_PROXIES)
            rl_key = build_rate_limit_key(
                tier.value, client_ip, request.url.path, request.method
            )
            rl_result = rate_limiter.check_rate_limit(rl_key, tier)
            if not rl_result.allowed:
                logger.warning(
                    "Rate limit exceeded: %s %s for %s (%s tier) - retry after %ss",
                    request.method,
                    request.url.path,
                    client_ip,
                    tier.value,
                    rl_result.retry_after,
                    extra={
                        "event": "rate_limit.rejected",
                        "request_id": req_id,
                        "client_ip": client_ip,
                        "tier": tier.value,
                        "retry_after": rl_result.retry_after,
                        "outcome": "rejected",
                    },
                )
                headers = {
                    "X-Request-ID": req_id,
                    "Retry-After": str(rl_result.retry_after),
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "Referrer-Policy": "strict-origin-when-cross-origin",
                }
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please try again later.",
                        },
                        "detail": "Too many requests. Please try again later.",
                    },
                    headers=headers,
                )

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Attach X-Request-ID and security headers
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Log request.completed
        logger.info(
            "Request completed: %s %s -> %s in %sms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "event": "request.completed",
                "request_id": req_id,
                "operation": f"{request.method} {request.url.path}",
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "outcome": "success" if response.status_code < 400 else "failure",
            },
        )
        return response
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            "Request failed: %s %s after %sms: %s",
            request.method,
            request.url.path,
            duration_ms,
            exc,
            extra={
                "event": "request.failed",
                "request_id": req_id,
                "operation": f"{request.method} {request.url.path}",
                "duration_ms": duration_ms,
                "outcome": "failure",
            },
            exc_info=True,
        )
        raise
    finally:
        set_current_request_id(None)


def make_error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    """Builds a deterministic error response compliant with both error DTO

    and backward-compatible detail, with X-Request-ID response header.
    """
    content = {
        "error": {
            "code": code,
            "message": message,
        },
        "detail": message,
    }
    if details:
        content["error"]["details"] = details

    headers = {}
    current_req_id = get_current_request_id()
    if current_req_id:
        headers["X-Request-ID"] = current_req_id

    return JSONResponse(status_code=status_code, content=content, headers=headers)


# --- 404 Resource Not Found Handlers ---
@app.exception_handler(ResourceNotFound)
async def resource_not_found_handler(request: Request, exc: ResourceNotFound):
    msg = str(exc) or "Requested resource was not found"
    logger.info(
        "Resource not found: %s",
        msg,
        extra={
            "event": "resource.not_found",
            "request_id": get_current_request_id(),
            "error_code": "RESOURCE_NOT_FOUND",
            "outcome": "failure",
        },
    )
    return make_error_response(404, "RESOURCE_NOT_FOUND", msg)


# --- 400 Validation Handlers ---
@app.exception_handler(InvalidChapter)
async def invalid_chapter_handler(request: Request, exc: InvalidChapter):
    logger.warning(
        "Invalid chapter access requested: %s",
        exc,
        extra={
            "event": "temporal.boundary_violation",
            "request_id": get_current_request_id(),
            "error_code": "INVALID_CHAPTER",
            "outcome": "failure",
        },
    )
    return make_error_response(400, "INVALID_CHAPTER", str(exc))


@app.exception_handler(AppValidationError)
async def app_validation_handler(request: Request, exc: AppValidationError):
    logger.info(
        "Application validation failed: %s",
        exc,
        extra={
            "event": "validation.failure",
            "request_id": get_current_request_id(),
            "error_code": "VALIDATION_ERROR",
            "outcome": "failure",
        },
    )
    return make_error_response(400, "VALIDATION_ERROR", str(exc))


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    logger.info(
        "Request schema validation failed for path: %s",
        request.url.path,
        extra={
            "event": "validation.failure",
            "request_id": get_current_request_id(),
            "error_code": "VALIDATION_ERROR",
            "outcome": "failure",
        },
    )
    return make_error_response(
        400,
        "VALIDATION_ERROR",
        "Request validation failed",
        {"errors": exc.errors()},
    )


# --- 409 Conflict Handlers ---
@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    msg = str(exc) or "Resource conflict detected"
    logger.warning(
        "Resource conflict: %s",
        msg,
        extra={
            "event": "resource.conflict",
            "request_id": get_current_request_id(),
            "error_code": "CONFLICT",
            "outcome": "failure",
        },
    )
    return make_error_response(409, "CONFLICT", msg)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning(
        "Database integrity conflict: %s",
        exc,
        extra={
            "event": "database.integrity_conflict",
            "request_id": get_current_request_id(),
            "error_code": "CONFLICT",
            "outcome": "failure",
        },
    )
    return make_error_response(
        409,
        "CONFLICT",
        "Operation violates a database integrity constraint",
    )


# --- 503 / 504 Database / Infrastructure Handlers ---
@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    logger.error(
        "Database operational error: %s",
        exc,
        extra={
            "event": "database.operation.failed",
            "request_id": get_current_request_id(),
            "error_code": "SERVICE_UNAVAILABLE",
            "outcome": "failure",
        },
    )
    return make_error_response(
        503,
        "SERVICE_UNAVAILABLE",
        "Database service is temporarily unavailable",
    )


@app.exception_handler(SATimeoutError)
async def timeout_error_handler(request: Request, exc: SATimeoutError):
    logger.error(
        "Database timeout error: %s",
        exc,
        extra={
            "event": "database.operation.timeout",
            "request_id": get_current_request_id(),
            "error_code": "GATEWAY_TIMEOUT",
            "outcome": "failure",
        },
    )
    return make_error_response(504, "GATEWAY_TIMEOUT", "Database operation timed out")


@app.exception_handler(DatabaseUnavailable)
async def db_unavailable_handler(request: Request, exc: DatabaseUnavailable):
    logger.error(
        "Database unavailable: %s",
        exc,
        extra={
            "event": "database.connection.failure",
            "request_id": get_current_request_id(),
            "error_code": "SERVICE_UNAVAILABLE",
            "outcome": "failure",
        },
    )
    return make_error_response(
        503,
        "SERVICE_UNAVAILABLE",
        "Database service is temporarily unavailable",
    )


@app.exception_handler(DatabaseTimeout)
async def db_timeout_handler(request: Request, exc: DatabaseTimeout):
    logger.error(
        "Database query timeout: %s",
        exc,
        extra={
            "event": "database.operation.timeout",
            "request_id": get_current_request_id(),
            "error_code": "GATEWAY_TIMEOUT",
            "outcome": "failure",
        },
    )
    return make_error_response(504, "GATEWAY_TIMEOUT", "Database operation timed out")


@app.exception_handler(TransactionFailure)
async def transaction_failure_handler(request: Request, exc: TransactionFailure):
    logger.error(
        "Transaction failure: %s",
        exc,
        extra={
            "event": "database.transaction.rollback",
            "request_id": get_current_request_id(),
            "error_code": "TRANSACTION_FAILURE",
            "outcome": "failure",
        },
    )
    return make_error_response(
        500, "TRANSACTION_FAILURE", "Transaction failed to complete"
    )


@app.exception_handler(SQLAlchemyError)
async def general_sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error(
        "Unhandled database error: %s",
        exc,
        extra={
            "event": "database.operation.failed",
            "request_id": get_current_request_id(),
            "error_code": "SERVICE_UNAVAILABLE",
            "outcome": "failure",
        },
    )
    return make_error_response(503, "SERVICE_UNAVAILABLE", "Database error occurred")


# --- 500 Unhandled Exceptions ---
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled server exception: %s",
        exc,
        exc_info=True,
        extra={
            "event": "server.unhandled_exception",
            "request_id": get_current_request_id(),
            "error_code": "INTERNAL_SERVER_ERROR",
            "outcome": "failure",
        },
    )
    return make_error_response(
        500,
        "INTERNAL_SERVER_ERROR",
        "An unexpected internal server error occurred",
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe: verifies process is alive and responsive."""
    return {"status": "ok", "service": "timeline-api"}


@app.get("/ready", tags=["Health"])
def readiness_check():
    """Readiness probe: verifies database connectivity safely without exposing credentials."""
    from sqlalchemy import text

    from apps.api.app.dependencies.database import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        logger.error(
            "Readiness check failed: database ping error: %s",
            exc,
            extra={
                "event": "database.connection.failure",
                "error_code": "SERVICE_UNAVAILABLE",
                "outcome": "failure",
            },
        )
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": "database unavailable"},
        )
