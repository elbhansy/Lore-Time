"""Tests for Milestone 4.6.6: Database Failure Logging."""

import logging
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as SATimeoutError

from apps.api.app.main import app


def test_database_operational_error_logging(caplog):
    """Verifies that database operational failures log structured database.operation.failed events."""
    client = TestClient(app)
    caplog.set_level(logging.ERROR)

    with patch(
        "apps.api.app.application.timeline.get_world_state.GetWorldStateUseCase.execute",
        side_effect=OperationalError("SELECT 1", {}, Exception("Connection refused")),
    ):
        response = client.get(
            "/api/v1/series/00000000-0000-0000-0000-000000000001/world-state?chapter=1"
        )
        assert response.status_code == 503

        db_records = [
            r
            for r in caplog.records
            if getattr(r, "event", None) == "database.operation.failed"
        ]
        assert len(db_records) >= 1
        assert db_records[0].error_code == "SERVICE_UNAVAILABLE"


def test_database_timeout_error_logging(caplog):
    """Verifies that database timeout errors log structured database.operation.timeout events."""
    client = TestClient(app)
    caplog.set_level(logging.ERROR)

    with patch(
        "apps.api.app.application.timeline.get_world_state.GetWorldStateUseCase.execute",
        side_effect=SATimeoutError("Queue pool limit reached", {}, None),
    ):
        response = client.get(
            "/api/v1/series/00000000-0000-0000-0000-000000000001/world-state?chapter=1"
        )
        assert response.status_code == 504

        timeout_records = [
            r
            for r in caplog.records
            if getattr(r, "event", None) == "database.operation.timeout"
        ]
        assert len(timeout_records) >= 1
        assert timeout_records[0].error_code == "GATEWAY_TIMEOUT"
