import uuid

import pytest
from fastapi.testclient import TestClient

from apps.api.app.application.exceptions import InvalidChapter, SeriesNotFound
from apps.api.app.dependencies.services import get_world_state_use_case
from apps.api.app.main import app
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId

client = TestClient(app)


class MockGetWorldStateUseCase:
    def execute(self, series_id: uuid.UUID, reader_chapter: int):
        if reader_chapter < 1:
            raise InvalidChapter("Invalid")
        if str(series_id) == "00000000-0000-0000-0000-000000000000":
            raise SeriesNotFound("Not found")

        return WorldState(
            series_id=EntityId(series_id), chapter=ChapterNumber(reader_chapter)
        )


@pytest.fixture(autouse=True)
def setup_world_state_override():
    app.dependency_overrides[get_world_state_use_case] = MockGetWorldStateUseCase
    yield
    app.dependency_overrides.pop(get_world_state_use_case, None)


def test_get_world_state_success():
    sid = str(uuid.uuid4())
    response = client.get(f"/api/v1/series/{sid}/world-state?chapter=10")
    assert response.status_code == 200
    data = response.json()
    assert data["series_id"] == sid
    assert data["chapter"] == 10
    assert data["characters"] == {}


def test_get_world_state_invalid_chapter():
    sid = str(uuid.uuid4())
    response = client.get(f"/api/v1/series/{sid}/world-state?chapter=-1")
    assert response.status_code == 400


def test_get_world_state_series_not_found():
    sid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/series/{sid}/world-state?chapter=10")
    assert response.status_code == 404
