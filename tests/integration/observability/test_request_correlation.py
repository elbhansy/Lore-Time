"""Tests for Milestone 4.6.3 and 4.6.4: Request Correlation and Lifecycle Logging."""

import logging
import uuid

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_request_correlation_auto_generated(caplog):
    """Verifies that an incoming request without X-Request-ID gets a generated UUID,

    which is propagated to response headers and log records.
    """
    client = TestClient(app)
    caplog.set_level(logging.INFO)

    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    req_id = response.headers["X-Request-ID"]
    assert len(req_id) > 10

    # Verify log messages captured with this request_id
    found_started = False
    found_completed = False
    for record in caplog.records:
        if getattr(record, "request_id", None) == req_id:
            if getattr(record, "event", None) == "request.started":
                found_started = True
            elif getattr(record, "event", None) == "request.completed":
                found_completed = True
                assert getattr(record, "duration_ms", None) is not None
                assert record.status_code == 200

    assert found_started, "request.started event not logged with correlation ID"
    assert found_completed, "request.completed event not logged with correlation ID"


def test_request_correlation_client_supplied_valid(caplog):
    """Verifies that client-supplied valid X-Request-ID is honored, echoed, and logged."""
    client = TestClient(app)
    caplog.set_level(logging.INFO)

    custom_id = f"trace-{uuid.uuid4()}"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id

    # Check logs
    matched_records = [
        r for r in caplog.records if getattr(r, "request_id", None) == custom_id
    ]
    assert len(matched_records) >= 2


def test_request_correlation_client_supplied_malformed_is_sanitized(caplog):
    """Verifies that a malformed client-supplied X-Request-ID (e.g. containing newlines or injection)

    is rejected and replaced with a clean generated UUID.
    """
    client = TestClient(app)
    caplog.set_level(logging.INFO)

    malformed_id = "malformed\r\ninjected_log_header_with_too_many_characters_and_invalid_symbols!!!"
    response = client.get("/health", headers={"X-Request-ID": malformed_id})
    assert response.status_code == 200
    returned_id = response.headers["X-Request-ID"]
    assert returned_id != malformed_id
    assert "\r" not in returned_id
    assert "\n" not in returned_id
