from packages.domain.entities.event import Event
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.services.power_progression import PowerProgressionService
from packages.domain.services.rank_comparison import RankComparisonService
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def _create_event(seq, ch, sub_id, new_rank):
    return Event(
        id=EntityId(f"e{seq}"),
        series_id=EntityId("s1"),
        chapter_id=EntityId(f"c{ch}"),
        sequence=seq,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId(sub_id),
        new_state={"power_system_id": "sys1", "rank_id": new_rank},
    )


def test_power_progression_determinism():
    state = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(200))
    applier = EventApplier()

    # We apply events exactly chronologically as they would arrive
    e1 = _create_event(1, 10, "char1", "rank_d")
    e2 = _create_event(2, 50, "char1", "rank_c")
    e3 = _create_event(3, 150, "char1", "rank_b")

    applier.apply(state, EventEnvelope(e1, ChapterNumber(10)))
    applier.apply(state, EventEnvelope(e2, ChapterNumber(50)))
    applier.apply(state, EventEnvelope(e3, ChapterNumber(150)))

    # Test at Chapter 100
    prog = PowerProgressionService.get_progression(state, "char1", "sys1", 100)
    assert prog.current_rank == "rank_c"
    assert len(prog.transitions) == 2

    # Test at Chapter 200
    prog200 = PowerProgressionService.get_progression(state, "char1", "sys1", 200)
    assert prog200.current_rank == "rank_b"
    assert len(prog200.transitions) == 3


def test_rank_comparison():
    res = RankComparisonService.compare("A", "sys1", "r1", 5, "B", "sys1", "r2", 4)
    assert res == "A_HIGHER"

    res = RankComparisonService.compare("A", "sys1", "r1", 5, "B", "sys2", "r2", 10)
    assert res == "NOT_COMPARABLE"


def test_breakthrough_detection():
    assert RankComparisonService.detect_breakthrough(1, 2) == "BREAKTHROUGH"
    assert RankComparisonService.detect_breakthrough(5, 3) == "REGRESSION"
    assert RankComparisonService.detect_breakthrough(2, 2) == "NO_CHANGE"
