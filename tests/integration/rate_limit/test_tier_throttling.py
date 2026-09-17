"""Integration tests for Tier-based Throttling (Expensive vs Standard)."""

import uuid

from fastapi.testclient import TestClient

from apps.api.app.config import get_settings
from apps.api.app.core.rate_limit import get_rate_limit_service
from apps.api.app.main import app


def test_expensive_endpoints_throttled_at_lower_threshold():
    """Expensive endpoints (WorldState, Analytics, Search) must be throttled at
    RATE_LIMIT_EXPENSIVE_BURST (10), while standard reads have higher capacity (30).
    """
    settings = get_settings()
    limiter = get_rate_limit_service()
    limiter.clear()

    client = TestClient(app)
    sid = uuid.uuid4()

    expensive_burst = settings.RATE_LIMIT_EXPENSIVE_BURST  # 10

    # 1. Fire allowable expensive requests (WorldState)
    for _ in range(expensive_burst):
        resp = client.get(f"/api/v1/series/{sid}/world-state?chapter=1")
        assert resp.status_code != 429

    # 2. 11th request to expensive endpoint must trip 429
    blocked_expensive = client.get(f"/api/v1/series/{sid}/world-state?chapter=1")
    assert blocked_expensive.status_code == 429
    assert blocked_expensive.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    # 3. Standard endpoint (under standard tier bucket) is NOT blocked by expensive tier consumption
    resp_standard = client.get(f"/api/v1/series/{sid}")
    assert resp_standard.status_code != 429
