from packages.domain.entities.event import Event
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.services.power_progression import PowerProgressionService
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def test_power_progression_deterministic_order():
    char_id = EntityId("char-1")

    # B at ch 20, A at ch 50, S at ch 100
    e1 = Event(
        id=EntityId("1"),
        chapter_id=EntityId("c1"),
        sequence=1,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_id,
        target_type=None,
        target_id=None,
        previous_state={},
        new_state={"rank_id": "B"},
    )
    e2 = Event(
        id=EntityId("2"),
        chapter_id=EntityId("c2"),
        sequence=1,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_id,
        target_type=None,
        target_id=None,
        previous_state={"rank_id": "B"},
        new_state={"rank_id": "A"},
    )
    e3 = Event(
        id=EntityId("3"),
        chapter_id=EntityId("c3"),
        sequence=1,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_id,
        target_type=None,
        target_id=None,
        previous_state={"rank_id": "A"},
        new_state={"rank_id": "S"},
    )

    env1 = EventEnvelope(e1, ChapterNumber(20))
    env2 = EventEnvelope(e2, ChapterNumber(50))
    env3 = EventEnvelope(e3, ChapterNumber(100))

    # Assuming envelopes are already sorted chronologically (as required by the service contract)
    envelopes = [env1, env2, env3]

    # Reader chapter 50 -> should only see B and A
    history_at_50 = PowerProgressionService.get_rank_history(char_id, envelopes, 50)
    assert len(history_at_50) == 2
    assert history_at_50[0].value == "B"
    assert history_at_50[1].value == "A"

    # Reader chapter 100 -> sees all
    history_at_100 = PowerProgressionService.get_rank_history(char_id, envelopes, 100)
    assert len(history_at_100) == 3
    assert history_at_100[2].value == "S"
