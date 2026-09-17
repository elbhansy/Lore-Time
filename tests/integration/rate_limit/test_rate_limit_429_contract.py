"""Integration tests for HTTP 429 Too Many Requests contract and Retry-After."""

import uuid

from fastapi.testclient import TestClient

from apps.api.app.config import get_settings
from apps.api.app.core.rate_limit import get_rate_limit_service
from apps.api.app.main import app


def test_rate_limit_429_contract_and_retry_after():
    """Verify standard error response structure and Retry-After header upon throttling."""
    settings = get_settings()
    limiter = get_rate_limit_service()
    limiter.clear()

    client = TestClient(app)
    sid = uuid.uuid4()

    # Standard endpoint limit is 120 req/min, burst is 30
    # Send requests until burst is exceeded
    burst_limit = settings.RATE_LIMIT_DEFAULT_BURST

    # Send allowable burst
    for _ in range(burst_limit):
        resp = client.get(f"/api/v1/series/{sid}")
        # Could be 200 or 404 depending on db seed, but must NOT be 429
        assert resp.status_code != 429

    # Next request must be throttled with 429
    blocked_resp = client.get(f"/api/v1/series/{sid}")
    assert blocked_resp.status_code == 429

    # Verify headers
    assert "Retry-After" in blocked_resp.headers
    retry_after = int(blocked_resp.headers["Retry-After"])
    assert retry_after >= 1
    assert blocked_resp.headers["X-Content-Type-Options"] == "nosniff"
    assert blocked_resp.headers["X-Frame-Options"] == "DENY"

    # Verify standard API error payload contract
    data = blocked_resp.json()
    assert "error" in data
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Too many requests" in data["error"]["message"]
    assert "detail" in data
