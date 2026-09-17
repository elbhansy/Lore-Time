import uuid

import pytest
from fastapi.testclient import TestClient

from apps.api.app.dependencies.services import get_timeline_events_use_case
from apps.api.app.main import app
from packages.domain.entities.event import Event
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType

client = TestClient(app)


class MockGetTimelineEventsUseCase:
    def execute(
        self,
        series_id: uuid.UUID,
        reader_chapter: int,
        from_chapter: int,
        to_chapter: int,
    ):
        e = Event(
            id=EntityId.generate(),
            series_id=EntityId(series_id),
            chapter_id=EntityId.generate(),
            sequence=1,
            type=EventType.CHARACTER_INTRODUCED,
            subject_type=EntityType.CHARACTER,
            subject_id=EntityId.generate(),
        )
        return [EventEnvelope(event=e, chapter_number=ChapterNumber(10))]


@pytest.fixture(autouse=True)
def setup_timeline_override():
    app.dependency_overrides[get_timeline_events_use_case] = (
        MockGetTimelineEventsUseCase
    )
    yield
    app.dependency_overrides.pop(get_timeline_events_use_case, None)


def test_get_timeline_events_success():
    sid = str(uuid.uuid4())
    response = client.get(
        f"/api/v1/series/{sid}/timeline?reader_chapter=50&from=1&to=50"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["chapter_number"] == 10
    assert data[0]["type"] == "CHARACTER_INTRODUCED"
