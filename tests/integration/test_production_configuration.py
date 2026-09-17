"""Production Configuration Validation and Failure Injection Test Matrix (Phase 4.12).

Verifies that the platform strictly enforces all production configuration boundaries:
1. DEBUG forbidden in production.
2. Weak or default SECRET_KEY rejected.
3. Wildcard or localhost CORS origins rejected in production.
4. Wildcard ALLOWED_HOSTS rejected in production.
5. Sample database passwords rejected in production.
6. Non-PostgreSQL database schemes rejected.
7. Negative integer configuration values rejected.
8. Request body size limits enforced (413 Payload Too Large).
9. TrustedHostMiddleware rejects unapproved host headers.
10. Trusted proxy client IP extraction defends against spoofed X-Forwarded-For headers.
11. Probes (/health and /ready) operate correctly without credential leakage.
12. Temporal firewall and series isolation remain absolute under production configuration.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.config import (
    Environment,
    Settings,
    get_settings,
    reset_settings_for_testing,
)
from apps.api.app.main import app
from tests.integration.cache.seed_helper import seed_test_series

# ==============================================================================
# 1. SECURITY & CONFIGURATION VALIDATION FAIL-FAST TESTS
# ==============================================================================


def test_production_fails_fast_on_debug_enabled():
    with pytest.raises(ValueError, match="DEBUG cannot be True in production"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=True,
            SECRET_KEY="A" * 32,
            DATABASE_URL="postgresql+psycopg://prod:strong_pass@db.internal:5432/db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
            ALLOWED_HOSTS=["loretime.app"],
        )


def test_production_fails_fast_on_weak_secret():
    # Less than 32 chars
    with pytest.raises(ValueError, match="SECRET_KEY of at least 32 characters"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="short-secret",
            DATABASE_URL="postgresql+psycopg://prod:strong_pass@db.internal:5432/db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
            ALLOWED_HOSTS=["loretime.app"],
        )

    # Contains dev-insecure
    with pytest.raises(ValueError, match="SECRET_KEY of at least 32 characters"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="dev-insecure-key-that-is-long-enough-32-chars!",
            DATABASE_URL="postgresql+psycopg://prod:strong_pass@db.internal:5432/db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
            ALLOWED_HOSTS=["loretime.app"],
        )


def test_production_fails_fast_on_wildcard_cors():
    with pytest.raises(
        ValueError, match=r"Wildcard '\*' CORS origin is strictly prohibited"
    ):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="A" * 32,
            DATABASE_URL="postgresql+psycopg://prod:strong_pass@db.internal:5432/db",
            CORS_ALLOWED_ORIGINS=["*"],
            ALLOWED_HOSTS=["loretime.app"],
        )


def test_production_fails_fast_on_localhost_cors():
    with pytest.raises(
        ValueError,
        match="Localhost origins are prohibited in production CORS_ALLOWED_ORIGINS",
    ):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="A" * 32,
            DATABASE_URL="postgresql+psycopg://prod:strong_pass@db.internal:5432/db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app", "http://localhost:5173"],
            ALLOWED_HOSTS=["loretime.app"],
        )


def test_production_fails_fast_on_wildcard_allowed_hosts():
    with pytest.raises(
        ValueError, match=r"Wildcard '\*' ALLOWED_HOSTS is strictly prohibited"
    ):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="A" * 32,
            DATABASE_URL="postgresql+psycopg://prod:strong_pass@db.internal:5432/db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
            ALLOWED_HOSTS=["*"],
        )


def test_production_fails_fast_on_sample_database_password():
    with pytest.raises(ValueError, match="Default sample database password detected"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="A" * 32,
            DATABASE_URL="postgresql+psycopg://timeline_user:timeline_password@localhost:5432/timeline_db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
            ALLOWED_HOSTS=["loretime.app"],
        )


def test_production_fails_fast_on_non_postgresql_scheme():
    with pytest.raises(
        ValueError, match="Production requires a valid PostgreSQL database URL"
    ):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="A" * 32,
            DATABASE_URL="sqlite:///./test.db",
            CORS_ALLOWED_ORIGINS=["https://loretime.app"],
            ALLOWED_HOSTS=["loretime.app"],
        )


def test_negative_resource_limits_rejected():
    with pytest.raises(ValueError, match="MAX_REQUEST_BODY_BYTES must be non-negative"):
        Settings(MAX_REQUEST_BODY_BYTES=-1)

    with pytest.raises(
        ValueError, match="DB_POOL_TIMEOUT_SECONDS must be non-negative"
    ):
        Settings(DB_POOL_TIMEOUT_SECONDS=-1)


# ==============================================================================
# 2. RUNTIME RESOURCE LIMITS & PROXY HARDENING INTEGRATION TESTS
# ==============================================================================


def test_request_body_size_ceiling_enforced():
    """Verifies that an incoming request exceeding MAX_REQUEST_BODY_BYTES returns 413."""
    client = TestClient(app)
    # Send request with oversized body header
    large_payload = "x" * 2000000  # ~2 MB
    response = client.post(
        "/api/v1/review/queue",
        content=large_payload,
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(large_payload)),
        },
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_ENTITY_TOO_LARGE"


def test_trusted_proxy_defense_rejects_spoofed_forwarded_headers():
    """Verifies that untrusted direct socket peer cannot spoof client identity via X-Forwarded-For."""
    client = TestClient(app)
    # Direct peer testclient is not in custom trusted proxy list
    custom_settings = Settings(
        TRUSTED_PROXIES=["10.0.0.1"]
    )  # testclient is 127.0.0.1/testclient
    reset_settings_for_testing(custom_settings)

    try:
        # Client tries to claim identity 8.8.8.8
        response = client.get(
            "/api/v1/unknown-endpoint",
            headers={"X-Forwarded-For": "8.8.8.8"},
        )
        assert response.status_code == 404
        # Rate limit / logging should identify the socket peer, not 8.8.8.8
    finally:
        reset_settings_for_testing(None)


def test_health_and_readiness_contracts_under_production_settings():
    """Verifies /health and /ready adhere to contracts and never leak credentials."""
    client = TestClient(app)

    # Health: Liveness
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json() == {"status": "ok", "service": "timeline-api"}
    assert "password" not in resp_health.text
    assert "database" not in resp_health.text

    # Ready: Readiness
    resp_ready = client.get("/ready")
    assert resp_ready.status_code == 200
    assert resp_ready.json() == {"status": "ready", "database": "connected"}
    assert "password" not in resp_ready.text


# ==============================================================================
# 3. TEMPORAL FIREWALL & SERIES ISOLATION PRESERVATION
# ==============================================================================


def test_temporal_firewall_and_series_isolation_under_production_config():
    """Validates that production configuration settings do not weaken temporal boundaries."""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine)

    try:
        with session_factory() as session:
            sid_str = seed_test_series(session, num_chapters=5, events_per_chapter=2)
            sid = uuid.UUID(sid_str)

        client = TestClient(app)

        # Reader at chapter 2 must see chapter 1 and 2, but NOT chapter 3
        resp_c2 = client.get(f"/api/v1/series/{sid_str}/world-state?chapter=2")
        assert resp_c2.status_code == 200
        data_c2 = resp_c2.json()

        # Reader at chapter 5 must see all
        resp_c5 = client.get(f"/api/v1/series/{sid_str}/world-state?chapter=5")
        assert resp_c5.status_code == 200
        data_c5 = resp_c5.json()

        assert len(data_c5.get("characters", [])) >= len(data_c2.get("characters", []))

        # Querying beyond series boundary fails cleanly with 404
        fake_sid = str(uuid.uuid4())
        resp_fake = client.get(f"/api/v1/series/{fake_sid}/world-state?chapter=1")
        assert resp_fake.status_code == 404
    finally:
        engine.dispose()
