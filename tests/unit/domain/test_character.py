import pytest

from packages.domain.entities.character import Character
from packages.domain.value_objects.entity_id import EntityId


def test_character_valid():
    series_id = EntityId.generate()
    c = Character(
        id=EntityId.generate(),
        series_id=series_id,
        name="Jinwoo",
        description="Shadow Monarch",
    )
    assert c.series_id == series_id
    assert c.name == "Jinwoo"


def test_character_empty_name_invalid():
    with pytest.raises(ValueError):
        Character(
            id=EntityId.generate(),
            series_id=EntityId.generate(),
            name="",
            description="Desc",
        )
