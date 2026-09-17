from packages.domain.entities.event import Event
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.services.world_state_builder import WorldStateBuilder
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def test_temporal_relationship_reconstruction():
    builder = WorldStateBuilder(EventApplier())
    series_id = EntityId("s1")
    char_a = EntityId("A")
    char_b = EntityId("B")

    # Ch.10: A -> FRIEND -> B
    e1 = Event(
        id=EntityId("1"),
        chapter_id=EntityId("c1"),
        sequence=1,
        type=EventType.RELATIONSHIP_CREATED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_a,
        target_type=EntityType.CHARACTER,
        target_id=char_b,
        previous_state={},
        new_state={"relationship_type": "FRIEND"},
        metadata={"chapter_number": 10},
    )

    # Ch.50: A -> ALLY -> B
    e2 = Event(
        id=EntityId("2"),
        chapter_id=EntityId("c2"),
        sequence=1,
        type=EventType.RELATIONSHIP_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_a,
        target_type=EntityType.CHARACTER,
        target_id=char_b,
        previous_state={"relationship_type": "FRIEND"},
        new_state={"relationship_type": "ALLY"},
        metadata={"chapter_number": 50},
    )

    # Ch.100: A -> ENEMY -> B
    e3 = Event(
        id=EntityId("3"),
        chapter_id=EntityId("c3"),
        sequence=1,
        type=EventType.RELATIONSHIP_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_a,
        target_type=EntityType.CHARACTER,
        target_id=char_b,
        previous_state={"relationship_type": "ALLY"},
        new_state={"relationship_type": "ENEMY"},
        metadata={"chapter_number": 100},
    )

    envs = [
        EventEnvelope(e1, ChapterNumber(10)),
        EventEnvelope(e2, ChapterNumber(50)),
        EventEnvelope(e3, ChapterNumber(100)),
    ]

    key = ("A", "B")

    # At ch 49 -> FRIEND
    state_49 = builder.build(series_id, envs, ChapterNumber(49))
    assert state_49.relationships[key].relationship_type.value == "FRIEND"

    # At ch 50 -> ALLY
    state_50 = builder.build(series_id, envs, ChapterNumber(50))
    assert state_50.relationships[key].relationship_type.value == "ALLY"

    # At ch 100 -> ENEMY
    state_100 = builder.build(series_id, envs, ChapterNumber(100))
    assert state_100.relationships[key].relationship_type.value == "ENEMY"


def test_relationship_ended_sets_active_false():
    builder = WorldStateBuilder(EventApplier())
    series_id = EntityId("s1")

    e1 = Event(
        id=EntityId("1"),
        chapter_id=EntityId("c1"),
        sequence=1,
        type=EventType.RELATIONSHIP_CREATED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId("A"),
        target_type=EntityType.CHARACTER,
        target_id=EntityId("B"),
        previous_state={},
        new_state={"relationship_type": "ALLY"},
        metadata={"chapter_number": 10},
    )

    e2 = Event(
        id=EntityId("2"),
        chapter_id=EntityId("c2"),
        sequence=1,
        type=EventType.RELATIONSHIP_ENDED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId("A"),
        target_type=EntityType.CHARACTER,
        target_id=EntityId("B"),
        previous_state={},
        new_state={},
        metadata={"chapter_number": 50},
    )

    envs = [EventEnvelope(e1, ChapterNumber(10)), EventEnvelope(e2, ChapterNumber(50))]

    state = builder.build(series_id, envs, ChapterNumber(100))
    assert state.relationships[("A", "B")].active is False
    assert state.relationships[("A", "B")].ended_at == 50
