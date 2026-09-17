"""Integration tests for Fail-Safe Degradation and Error Throttling."""

from fastapi.testclient import TestClient

from apps.api.app.core.rate_limit import (
    RateLimitService,
    reset_rate_limit_service_for_testing,
)
from apps.api.app.main import app


class BrokenLimiter:
    def check(self, key: str, limit: int, burst: int):
        raise RuntimeError("Simulated internal limiter crash")

    def clear(self):
        pass


def test_rate_limiter_failure_fails_open_gracefully():
    """Verify that if the limiter raises an unexpected internal exception,
    the service fails open (allows request) without returning 500 to client.
    """
    broken_service = RateLimitService(limiter=BrokenLimiter())
    reset_rate_limit_service_for_testing(broken_service)

    try:
        client = TestClient(app)
        # Even with a broken limiter, request must proceed safely
        resp = client.get("/health")
        assert resp.status_code == 200

        resp2 = client.get("/api/v1/series/12345678-1234-5678-1234-567812345678")
        assert resp2.status_code != 500
        assert resp2.status_code != 429
    finally:
        reset_rate_limit_service_for_testing(None)
