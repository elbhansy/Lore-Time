"""Tests for Milestone 4.6.8: Security Event Logging."""

import logging
import uuid

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_temporal_boundary_violation_logging(caplog):
    """Verifies that an illegal temporal range request (to_chapter > reader_chapter)

    logs temporal.boundary_violation event.
    """
    client = TestClient(app)
    caplog.set_level(logging.WARNING)

    fake_series = uuid.uuid4()
    # Requesting to_chapter=10 when reader_chapter=5
    response = client.get(
        f"/api/v1/series/{fake_series}/events?reader_chapter=5&from_chapter=1&to_chapter=10"
    )
    assert response.status_code == 400

    sec_records = [
        r
        for r in caplog.records
        if getattr(r, "event", None) == "temporal.boundary_violation"
    ]
    assert len(sec_records) >= 1
    assert sec_records[0].error_code == "INVALID_CHAPTER"
    assert sec_records[0].outcome == "failure"
