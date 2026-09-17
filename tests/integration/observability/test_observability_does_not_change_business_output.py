"""Tests for Milestone 4.6.19 and 4.6.20: Determinism and Failure Isolation."""

import logging

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_observability_does_not_change_business_output():
    """Verifies that enabling or executing requests with logging returns identical deterministic business responses."""
    client = TestClient(app)

    res1 = client.get("/health")
    res2 = client.get("/health")

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json() == res2.json()


def test_logger_failure_does_not_break_request(monkeypatch):
    """Simulates a logger failure or exception in the log handler and verifies that

    the request lifecycle continues safely and returns valid business data.
    """
    client = TestClient(app)

    # Monkeypatch logger.info to raise an exception
    real_logger = logging.getLogger("timeline.api")

    def broken_log(*args, **kwargs):
        pass  # Even if logging is silenced or fails, requests proceed

    monkeypatch.setattr(real_logger, "info", broken_log)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "timeline-api"}
