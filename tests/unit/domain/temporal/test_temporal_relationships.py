from packages.domain.entities.event import Event
from packages.domain.services.event_applier import EventApplier
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def test_relationship_evolution():
    state = WorldState(series_id=EntityId.generate(), chapter=ChapterNumber(1))
    applier = EventApplier()
    subj = EntityId.generate()
    targ = EntityId.generate()
    key = (subj, targ)

    # 1. Create Enemy
    e1 = Event(
        id=EntityId.generate(),
        series_id=state.series_id,
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.RELATIONSHIP_CREATED,
        subject_type=EntityType.CHARACTER,
        subject_id=subj,
        target_type=EntityType.CHARACTER,
        target_id=targ,
        new_state={"relationship_type": "ENEMY"},
    )
    applier.apply(state, e1)

    assert key in state.relationships
    assert state.relationships[key].active
    assert state.relationships[key].relationship_type == "ENEMY"

    # 2. Change to Ally
    e2 = Event(
        id=EntityId.generate(),
        series_id=state.series_id,
        chapter_id=EntityId.generate(),
        sequence=2,
        type=EventType.RELATIONSHIP_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=subj,
        target_type=EntityType.CHARACTER,
        target_id=targ,
        new_state={"relationship_type": "ALLY"},
    )
    applier.apply(state, e2)
    assert state.relationships[key].relationship_type == "ALLY"

    # 3. End relationship
    e3 = Event(
        id=EntityId.generate(),
        series_id=state.series_id,
        chapter_id=EntityId.generate(),
        sequence=3,
        type=EventType.RELATIONSHIP_ENDED,
        subject_type=EntityType.CHARACTER,
        subject_id=subj,
        target_type=EntityType.CHARACTER,
        target_id=targ,
    )
    applier.apply(state, e3)
    assert not state.relationships[key].active
