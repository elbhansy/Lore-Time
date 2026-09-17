from packages.domain.entities.event import Event
from packages.domain.services.event_applier import EventApplier
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def test_character_lifecycle():
    state = WorldState(series_id=EntityId.generate(), chapter=ChapterNumber(1))
    applier = EventApplier()
    char_id = EntityId.generate()

    # Introduce
    e1 = Event(
        id=EntityId.generate(),
        series_id=state.series_id,
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.CHARACTER_INTRODUCED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_id,
    )
    applier.apply(state, e1)

    assert char_id in state.characters
    assert state.characters[char_id].exists
    assert state.characters[char_id].alive

    # Die
    e2 = Event(
        id=EntityId.generate(),
        series_id=state.series_id,
        chapter_id=EntityId.generate(),
        sequence=2,
        type=EventType.CHARACTER_DIED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_id,
    )
    applier.apply(state, e2)
    assert not state.characters[char_id].alive


def test_power_rank():
    state = WorldState(series_id=EntityId.generate(), chapter=ChapterNumber(1))
    applier = EventApplier()
    char_id = EntityId.generate()

    e = Event(
        id=EntityId.generate(),
        series_id=state.series_id,
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_id,
        new_state={"rank": "S"},
    )
    applier.apply(state, e)
    assert state.characters[char_id].rank == "S"
