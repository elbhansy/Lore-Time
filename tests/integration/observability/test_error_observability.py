"""Tests for Milestone 4.6.10: Error Observability and Semantic Classification."""

import logging
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.config import get_settings
from apps.api.app.main import app
from infrastructure.database.models import Base
from infrastructure.database.models.series import SeriesModel


@pytest.fixture
def obs_db():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


def test_validation_error_observability(caplog):
    """Verifies that 400 validation failures emit structured validation.failure events."""
    client = TestClient(app)
    caplog.set_level(logging.INFO)

    # Missing required query parameters triggers RequestValidationError
    fake_series = uuid.uuid4()
    response = client.get(f"/api/v1/series/{fake_series}/world-state")
    assert response.status_code == 400

    val_records = [
        r for r in caplog.records if getattr(r, "event", None) == "validation.failure"
    ]
    assert len(val_records) >= 1
    assert val_records[0].error_code == "VALIDATION_ERROR"
    assert val_records[0].outcome == "failure"


def test_resource_not_found_observability(obs_db, caplog):
    """Verifies that 404 domain errors emit structured resource.not_found events."""
    client = TestClient(app)
    caplog.set_level(logging.INFO)

    # Create one series so tables exist in DB
    existing_sid = uuid.uuid4()
    obs_db.add(
        SeriesModel(
            id=existing_sid,
            title="Existing Series",
            slug=f"ex-{str(existing_sid)[:8]}",
            total_chapters=5,
        )
    )
    obs_db.commit()

    non_existent_series = uuid.uuid4()
    response = client.get(f"/api/v1/series/{non_existent_series}/world-state?chapter=1")
    assert response.status_code == 404

    nf_records = [
        r for r in caplog.records if getattr(r, "event", None) == "resource.not_found"
    ]
    assert len(nf_records) >= 1
    assert nf_records[0].error_code == "RESOURCE_NOT_FOUND"
    assert nf_records[0].outcome == "failure"
