from packages.domain.entities.event import Event
from packages.domain.factions.faction_intelligence import FactionIntelligence
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def _create_event(seq, ch, typ, sub_id, new_state=None, target_id=None):
    return Event(
        id=EntityId(f"e{seq}"),
        series_id=EntityId("s1"),
        chapter_id=EntityId(f"c{ch}"),
        sequence=seq,
        type=typ,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId(sub_id),
        target_id=EntityId(target_id) if target_id else None,
        new_state=new_state or {},
    )


def test_multi_membership_and_intelligence():
    state = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(100))
    applier = EventApplier()

    # 1. A joins X at ch 10
    e1 = _create_event(1, 10, EventType.FACTION_MEMBER_JOINED, "A", target_id="X")
    # 2. A joins Y at ch 20
    e2 = _create_event(2, 20, EventType.FACTION_MEMBER_JOINED, "A", target_id="Y")
    # 3. A leaves X at ch 30
    e3 = _create_event(3, 30, EventType.FACTION_MEMBER_LEFT, "A", target_id="X")
    # 4. A joins Z at ch 40
    e4 = _create_event(4, 40, EventType.FACTION_MEMBER_JOINED, "A", target_id="Z")

    for e in [e1, e2, e3, e4]:
        env = EventEnvelope(
            event=e, chapter_number=ChapterNumber(int(e.chapter_id.value[1:]))
        )
        applier.apply(state, env)

    # At ch 40, A should be active in Y and Z, but not X.
    assert "A" not in FactionIntelligence.get_active_members(state, "X")
    assert "A" in FactionIntelligence.get_active_members(state, "Y")
    assert "A" in FactionIntelligence.get_active_members(state, "Z")

    # History for X should still show A
    x_hist = FactionIntelligence.get_membership_history(state, "X")
    assert len(x_hist) == 1
    assert x_hist[0].character_id == "A"
    assert x_hist[0].joined_at == 10
    assert x_hist[0].left_at == 30


def test_leadership_succession():
    state = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(100))
    applier = EventApplier()

    e1 = _create_event(
        1, 20, EventType.FACTION_LEADER_CHANGED, "X", new_state={"new_leader_id": "L1"}
    )
    e2 = _create_event(
        2,
        80,
        EventType.FACTION_LEADER_CHANGED,
        "X",
        new_state={"previous_leader_id": "L1", "new_leader_id": "L2"},
    )

    applier.apply(state, EventEnvelope(e1, ChapterNumber(20)))
    assert FactionIntelligence.get_current_leader(state, "X") == "L1"

    applier.apply(state, EventEnvelope(e2, ChapterNumber(80)))
    assert FactionIntelligence.get_current_leader(state, "X") == "L2"

    hist = FactionIntelligence.get_leadership_history(state, "X")
    assert len(hist) == 2
    assert hist[0].leader_id == "L2"
    assert hist[1].leader_id == "L1"
    assert hist[1].ended_at == 80
