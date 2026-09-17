from packages.domain.entities.event import Event
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def test_event_valid():
    e = Event(
        id=EntityId.generate(),
        series_id=EntityId.generate(),
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId.generate(),
        previous_state={"rank": "E"},
        new_state={"rank": "D"},
    )
    assert e.type == EventType.POWER_RANK_CHANGED
    assert e.new_state["rank"] == "D"
    assert e.sequence == 1
