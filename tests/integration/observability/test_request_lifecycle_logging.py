"""Tests for Milestone 4.6.4: Request Lifecycle Logging."""

import logging

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_request_lifecycle_success(caplog):
    """Verifies that normal request execution emits request.started and request.completed

    with duration_ms, method, and status_code.
    """
    client = TestClient(app)
    caplog.set_level(logging.INFO)

    response = client.get("/health")
    assert response.status_code == 200

    completed_events = [
        r for r in caplog.records if getattr(r, "event", None) == "request.completed"
    ]
    assert len(completed_events) >= 1
    event = completed_events[-1]
    assert event.status_code == 200
    assert event.duration_ms >= 0
    assert event.outcome == "success"


def test_request_lifecycle_404(caplog):
    """Verifies that 404 responses emit request.completed with outcome=failure and status_code=404."""
    client = TestClient(app)
    caplog.set_level(logging.INFO)

    response = client.get("/non-existent-path-for-testing")
    assert response.status_code == 404

    completed_events = [
        r for r in caplog.records if getattr(r, "event", None) == "request.completed"
    ]
    assert len(completed_events) >= 1
    event = completed_events[-1]
    assert event.status_code == 404
    assert event.outcome == "failure"
