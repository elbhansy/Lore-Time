import random

from packages.domain.entities.event import Event
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.services.world_state_builder import WorldStateBuilder
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def test_builder_spoiler_firewall_and_determinism():
    builder = WorldStateBuilder(EventApplier())
    series_id = EntityId.generate()
    char_id = EntityId.generate()

    def _make_env(ch: int, seq: int, rank: str) -> EventEnvelope:
        return EventEnvelope(
            chapter_number=ChapterNumber(ch),
            event=Event(
                id=EntityId.generate(),
                series_id=series_id,
                chapter_id=EntityId.generate(),
                sequence=seq,
                type=EventType.POWER_RANK_CHANGED,
                subject_type=EntityType.CHARACTER,
                subject_id=char_id,
                new_state={"rank": rank},
            ),
        )

    env1 = _make_env(10, 1, "C")
    env2 = _make_env(50, 1, "B")
    env3 = _make_env(100, 1, "A")
    env4 = _make_env(200, 1, "S")

    envelopes = [env1, env2, env3, env4]

    # Firewall Test
    state_50 = builder.build(series_id, envelopes, ChapterNumber(50))
    assert state_50.characters[char_id].rank == "B"

    state_99 = builder.build(series_id, envelopes, ChapterNumber(99))
    assert state_99.characters[char_id].rank == "B"

    state_150 = builder.build(series_id, envelopes, ChapterNumber(150))
    assert state_150.characters[char_id].rank == "A"

    # Determinism Test (shuffle inputs)
    shuffled_envelopes = list(envelopes)
    random.shuffle(shuffled_envelopes)

    state_shuffled_50 = builder.build(series_id, shuffled_envelopes, ChapterNumber(50))
    assert (
        state_shuffled_50 == state_50
    )  # dataclass equality deeply compares attributes


def test_temporal_firewall_boundary_triad():
    """
    Explicitly proves the triad:
    chapter = event.chapter - 1  -> INVISIBLE
    chapter = event.chapter      -> VISIBLE
    chapter = event.chapter + 1  -> VISIBLE
    """
    builder = WorldStateBuilder(EventApplier())
    series_id = EntityId("series-1")
    char_a = EntityId("A")
    char_b = EntityId("B")

    event_50 = Event(
        id=EntityId("e50"),
        chapter_id=EntityId("c50"),
        sequence=1,
        type=EventType.RELATIONSHIP_CREATED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_a,
        target_type=EntityType.CHARACTER,
        target_id=char_b,
        previous_state={},
        new_state={"relationship_type": "ALLY"},
        metadata={"chapter_number": 50},
    )
    envelopes = [EventEnvelope(event_50, ChapterNumber(50))]

    # Boundary 1: event.chapter - 1 (ch 49) -> INVISIBLE
    state_49 = builder.build(series_id, envelopes, ChapterNumber(49))
    assert ("A", "B") not in state_49.relationships

    # Boundary 2: event.chapter (ch 50) -> VISIBLE
    state_50 = builder.build(series_id, envelopes, ChapterNumber(50))
    assert ("A", "B") in state_50.relationships
    assert state_50.relationships[("A", "B")].relationship_type.value == "ALLY"
    assert state_50.relationships[("A", "B")].started_at == 50

    # Boundary 3: event.chapter + 1 (ch 51) -> VISIBLE
    state_51 = builder.build(series_id, envelopes, ChapterNumber(51))
    assert ("A", "B") in state_51.relationships
    assert state_51.relationships[("A", "B")].relationship_type.value == "ALLY"
