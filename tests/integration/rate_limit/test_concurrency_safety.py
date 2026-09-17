"""Integration tests for Concurrency Safety & Race Condition Defense."""

import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from apps.api.app.config import get_settings
from apps.api.app.core.rate_limit import get_rate_limit_service
from apps.api.app.main import app


def test_concurrent_requests_against_same_identity():
    """Verify that firing 30 simultaneous threads against a limit of 10
    allows exactly 10 requests and rejects exactly 20 with 429, with zero race conditions.
    """
    settings = get_settings()
    limiter = get_rate_limit_service()
    limiter.clear()

    client = TestClient(app)
    sid = uuid.uuid4()
    endpoint = f"/api/v1/series/{sid}/world-state?chapter=1"

    num_threads = 30
    burst_limit = settings.RATE_LIMIT_EXPENSIVE_BURST  # 10

    def make_req():
        return client.get(endpoint).status_code

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_req) for _ in range(num_threads)]
        status_codes = [f.result() for f in futures]

    allowed_count = sum(1 for c in status_codes if c != 429)
    rejected_count = sum(1 for c in status_codes if c == 429)

    # Exactly burst_limit must be allowed, and remaining rejected
    assert allowed_count == burst_limit
    assert rejected_count == num_threads - burst_limit
