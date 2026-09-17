import uuid

import pytest
from fastapi.testclient import TestClient

from apps.api.app.application.exceptions import CharacterNotFound
from apps.api.app.dependencies.services import get_character_use_case
from apps.api.app.main import app
from packages.domain.entities.character import Character
from packages.domain.state.character_state import CharacterState
from packages.domain.value_objects.entity_id import EntityId

client = TestClient(app)


class MockGetCharacterUseCase:
    def execute(
        self, series_id: uuid.UUID, character_id: uuid.UUID, reader_chapter: int
    ):
        if str(character_id) == "00000000-0000-0000-0000-000000000000":
            raise CharacterNotFound("Not found")

        char_ent = Character(
            id=EntityId(character_id),
            series_id=EntityId(series_id),
            name="Test Char",
            description="",
        )

        char_state = CharacterState(
            character_id=EntityId(character_id), exists=True, alive=True, rank="B"
        )
        return char_ent, char_state


@pytest.fixture(autouse=True)
def setup_character_override():
    app.dependency_overrides[get_character_use_case] = MockGetCharacterUseCase
    yield
    app.dependency_overrides.pop(get_character_use_case, None)


def test_get_character_success():
    sid = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    response = client.get(f"/api/v1/series/{sid}/characters/{cid}?chapter=20")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == cid
    assert data["name"] == "Test Char"
    assert data["as_of_chapter"] == 20
    assert data["state"]["alive"] is True
    assert data["state"]["rank"] == "B"


def test_get_character_not_found():
    sid = str(uuid.uuid4())
    cid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/series/{sid}/characters/{cid}?chapter=20")
    assert response.status_code == 404
