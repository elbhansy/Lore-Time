"""Integration tests for Invalid Request / 404 Probing consuming rate limit budget."""

import uuid

from fastapi.testclient import TestClient

from apps.api.app.config import get_settings
from apps.api.app.core.rate_limit import get_rate_limit_service
from apps.api.app.main import app


def test_invalid_requests_and_404s_consume_budget():
    """Verify that probing nonexistent endpoints or passing invalid parameters
    consumes rate limit budget, preventing attacker scanning.
    """
    settings = get_settings()
    limiter = get_rate_limit_service()
    limiter.clear()

    client = TestClient(app)
    burst = settings.RATE_LIMIT_DEFAULT_BURST  # 30

    # Probe nonexistent series IDs (returns 404)
    for _ in range(burst):
        bad_id = uuid.uuid4()
        resp = client.get(f"/api/v1/series/{bad_id}")
        assert resp.status_code == 404

    # 31st probe must trip 429
    blocked = client.get(f"/api/v1/series/{uuid.uuid4()}")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
