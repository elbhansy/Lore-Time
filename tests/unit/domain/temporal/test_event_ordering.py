from packages.domain.entities.event import Event
from packages.domain.services.event_ordering import EventEnvelope, sort_events
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def _create_env(chapter: int, sequence: int, id_str: str) -> EventEnvelope:
    e = Event(
        id=EntityId.from_string(id_str),
        series_id=EntityId.generate(),
        chapter_id=EntityId.generate(),
        sequence=sequence,
        type=EventType.CHARACTER_INTRODUCED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId.generate(),
    )
    return EventEnvelope(event=e, chapter_number=ChapterNumber(chapter))


def test_event_ordering():
    id_a = "00000000-0000-0000-0000-000000000001"
    id_b = "00000000-0000-0000-0000-000000000002"

    env1 = _create_env(chapter=10, sequence=1, id_str=id_a)
    env2 = _create_env(chapter=10, sequence=2, id_str=id_a)
    env3 = _create_env(chapter=10, sequence=2, id_str=id_b)
    env4 = _create_env(chapter=20, sequence=1, id_str=id_a)

    # Shuffled input
    envelopes = [env4, env2, env1, env3]
    sorted_envs = sort_events(envelopes)

    assert sorted_envs[0] == env1
    assert sorted_envs[1] == env2
    assert sorted_envs[2] == env3
    assert sorted_envs[3] == env4
