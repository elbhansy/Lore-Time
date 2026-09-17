import uuid

import pytest

from packages.domain.value_objects.entity_id import EntityId


def test_entity_id_generate():
    entity_id = EntityId.generate()
    assert isinstance(entity_id.value, uuid.UUID)


def test_entity_id_from_string_valid():
    valid_uuid_str = str(uuid.uuid4())
    entity_id = EntityId.from_string(valid_uuid_str)
    assert str(entity_id) == valid_uuid_str


def test_entity_id_from_string_invalid():
    with pytest.raises(ValueError):
        EntityId.from_string("invalid-uuid")


def test_entity_id_equality():
    valid_uuid_str = str(uuid.uuid4())
    id1 = EntityId.from_string(valid_uuid_str)
    id2 = EntityId.from_string(valid_uuid_str)
    assert id1 == id2
