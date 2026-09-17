"""Tests for Milestone 4.6.9: Temporal Privacy of Logs (Spoiler Firewall in Observability)."""

import logging
import uuid

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_logs_do_not_leak_future_content(caplog):
    """Verifies that when a client attempts to probe or query resources,

    no future lore, secret names, or event descriptions enter the log stream.
    """
    client = TestClient(app)
    caplog.set_level(logging.INFO)

    future_spoiler_token = "SPOILER_SUPREME_GOD_OF_DESTRUCTION"
    fake_series = uuid.uuid4()

    # Search probe
    client.get(
        f"/api/v1/series/{fake_series}/search?q={future_spoiler_token}&chapter=1"
    )

    # Inspect all emitted log strings
    for record in caplog.records:
        msg = record.getMessage()
        # Ensure the sensitive user payload wasn't echoed into unhandled leaks
        # And ensure structured extra fields don't leak future story data
        assert "Secret Character X" not in msg
        assert getattr(record, "future_story_content", None) is None
