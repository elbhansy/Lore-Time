"""Integration tests for Health and Readiness Probe rate limiting exemption."""

from fastapi.testclient import TestClient

from apps.api.app.core.rate_limit import (
    get_rate_limit_service,
)
from apps.api.app.main import app


def test_health_and_ready_exempt_from_rate_limiting():
    """Verify that flooding /health and /ready never triggers 429 Too Many Requests."""
    limiter_service = get_rate_limit_service()
    limiter_service.clear()

    client = TestClient(app)

    # 1. Flood /health with 200 consecutive requests
    for _ in range(200):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "service": "timeline-api"}

    # 2. Flood /ready with 100 consecutive requests
    for _ in range(100):
        resp = client.get("/ready")
        assert resp.status_code in (200, 503)  # Liveness / DB dependent, but NEVER 429
        assert resp.status_code != 429

    # Verify zero rejections
    stats = limiter_service.stats()
    assert stats.get("rejected", 0) == 0
