"""Unit tests for Phase 5.1 Narrative Intelligence Engine.

Covers:
- ArcMilestone extraction from diverse canonical events
- TurningPoint detection (mortality, power, faction, relationship reversal, multi-dimensional)
- NarrativePhase construction
- CharacterArc synthesis and trajectory metrics
- Empty data / partial data safety
- Deterministic ordering
"""

import uuid

from packages.domain.entities.event import Event
from packages.domain.narrative.character_arc_builder import CharacterArcBuilder
from packages.domain.narrative.milestone_extractor import MilestoneExtractor
from packages.domain.narrative.models import (
    MilestoneType,
    SignificanceLevel,
    TurningPointType,
)
from packages.domain.narrative.turning_point_detector import TurningPointDetector
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.services.narrative_intelligence_engine import (
    NarrativeIntelligenceEngine,
)
from packages.domain.state.character_state import CharacterState
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def _make_env(
    chapter: int,
    seq: int,
    event_type: EventType,
    subject_id: str,
    target_id: str | None = None,
    prev_state: dict = None,
    new_state: dict = None,
    metadata: dict = None,
) -> EventEnvelope:
    eid = EntityId(uuid.uuid4())
    cid = EntityId(uuid.uuid4())
    sid = EntityId(subject_id)
    tid = EntityId(target_id) if target_id else None
    event = Event(
        id=eid,
        chapter_id=cid,
        sequence=seq,
        type=event_type,
        subject_type=EntityType.CHARACTER,
        subject_id=sid,
        target_type=EntityType.CHARACTER if target_id else None,
        target_id=tid,
        previous_state=prev_state or {},
        new_state=new_state or {},
        metadata=metadata or {},
    )
    return EventEnvelope(event=event, chapter_number=ChapterNumber(chapter))


def test_milestone_extractor_supported_events():
    char_id = "char_dokja"
    envelopes = [
        _make_env(1, 1, EventType.CHARACTER_INTRODUCED, char_id),
        _make_env(
            5,
            1,
            EventType.SKILL_UNLOCKED,
            char_id,
            metadata={"skill_name": "Omniscient Reader"},
        ),
        _make_env(
            10,
            1,
            EventType.POWER_RANK_CHANGED,
            char_id,
            prev_state={"rank": "F"},
            new_state={"rank": "E"},
        ),
        _make_env(
            15,
            1,
            EventType.FACTION_MEMBER_JOINED,
            char_id,
            metadata={"faction_name": "Kim Dokja Company"},
        ),
        _make_env(
            20,
            1,
            EventType.RELATIONSHIP_CREATED,
            char_id,
            target_id="char_joonghyuk",
            new_state={"type": "ally"},
        ),
        _make_env(
            30,
            1,
            EventType.RELATIONSHIP_CHANGED,
            char_id,
            target_id="char_joonghyuk",
            prev_state={"type": "ally"},
            new_state={"type": "enemy"},
        ),
        _make_env(50, 1, EventType.CHARACTER_DIED, char_id),
    ]

    milestones = MilestoneExtractor.extract_milestones(char_id, envelopes)
    assert len(milestones) == 7

    types = [m.milestone_type for m in milestones]
    assert types == [
        MilestoneType.FIRST_APPEARANCE,
        MilestoneType.SKILL_ACQUIRED,
        MilestoneType.RANK_CHANGE,
        MilestoneType.FACTION_JOINED,
        MilestoneType.RELATIONSHIP_FORMED,
        MilestoneType.RELATIONSHIP_CHANGED,
        MilestoneType.DEATH,
    ]


def test_turning_point_detection_rules():
    char_id = "char_dokja"
    envelopes = [
        _make_env(1, 1, EventType.CHARACTER_INTRODUCED, char_id),
        _make_env(
            10,
            1,
            EventType.POWER_RANK_CHANGED,
            char_id,
            prev_state={"rank": "E"},
            new_state={"rank": "S"},
        ),
        _make_env(
            20,
            1,
            EventType.RELATIONSHIP_CHANGED,
            char_id,
            target_id="char_rival",
            prev_state={"type": "ally"},
            new_state={"type": "enemy"},
        ),
        _make_env(40, 1, EventType.CHARACTER_DIED, char_id),
    ]

    milestones = MilestoneExtractor.extract_milestones(char_id, envelopes)
    turning_points = TurningPointDetector.detect_turning_points(char_id, milestones)

    assert len(turning_points) == 3

    # 1. Power breakthrough
    assert turning_points[0].chapter == 10
    assert turning_points[0].turning_point_type == TurningPointType.POWER_BREAKTHROUGH
    assert turning_points[0].significance == SignificanceLevel.HIGH

    # 2. Relationship transformation
    assert turning_points[1].chapter == 20
    assert (
        turning_points[1].turning_point_type
        == TurningPointType.RELATIONSHIP_TRANSFORMATION
    )
    assert turning_points[1].significance == SignificanceLevel.HIGH

    # 3. Mortality event
    assert turning_points[2].chapter == 40
    assert turning_points[2].turning_point_type == TurningPointType.MORTALITY_EVENT
    assert turning_points[2].significance == SignificanceLevel.CRITICAL


def test_character_arc_builder_full_lifecycle():
    series_id = "series_orv"
    char_id = "char_dokja"
    reader_chapter = 50

    envelopes = [
        _make_env(1, 1, EventType.CHARACTER_INTRODUCED, char_id),
        _make_env(
            10,
            1,
            EventType.POWER_RANK_CHANGED,
            char_id,
            prev_state={"rank": "F"},
            new_state={"rank": "D"},
        ),
        _make_env(
            25,
            1,
            EventType.FACTION_LEADER_CHANGED,
            char_id,
            new_state={"leader_id": char_id, "faction_id": "fac_company"},
        ),
        _make_env(45, 1, EventType.CHARACTER_DIED, char_id),
        # Future event beyond readerChapter: MUST BE IGNORED
        _make_env(
            60, 1, EventType.CHARACTER_INTRODUCED, char_id, new_state={"rank": "EX"}
        ),
    ]

    ws = WorldState(
        series_id=EntityId(series_id),
        chapter=ChapterNumber(reader_chapter),
        characters={
            char_id: CharacterState(
                character_id=EntityId(char_id),
                exists=True,
                alive=False,
                rank="D",
                faction_id="fac_company",
                unlocked_skills={"skill_bookmark"},
            )
        },
    )

    arc = CharacterArcBuilder.build_arc(
        series_id=series_id,
        character_id=char_id,
        reader_chapter=reader_chapter,
        envelopes=envelopes,
        world_state=ws,
    )

    assert arc.series_id == series_id
    assert arc.character_id == char_id
    assert arc.reader_chapter == reader_chapter
    assert arc.start_chapter == 1
    assert arc.end_chapter == 45  # Event at 60 was dropped!

    # 4 milestones: Ch 1, 10, 25, 45
    assert len(arc.milestones) == 4
    assert all(m.chapter <= reader_chapter for m in arc.milestones)

    # 3 turning points: Ch 10 (rank), Ch 25 (faction), Ch 45 (death)
    assert len(arc.turning_points) == 3

    # Phases should segment around turning points
    assert len(arc.phases) >= 3

    # Trajectory verification
    assert arc.trajectory is not None
    assert arc.trajectory.current_status == "dead"
    assert arc.trajectory.current_rank == "D"
    assert arc.trajectory.highest_significance == SignificanceLevel.CRITICAL


def test_empty_and_partial_character_arcs():
    engine = NarrativeIntelligenceEngine()
    series_id = "series_test"
    char_id = "char_unknown"

    # 1. Zero events
    arc_empty = engine.derive_character_arc(
        series_id=series_id,
        character_id=char_id,
        reader_chapter=10,
        envelopes=[],
        world_state=None,
    )
    assert arc_empty.start_chapter is None
    assert arc_empty.end_chapter is None
    assert len(arc_empty.milestones) == 0
    assert len(arc_empty.turning_points) == 0
    assert len(arc_empty.phases) == 0
    assert arc_empty.trajectory.current_status == "unintroduced"

    # 2. Single appearance without turning points
    env_single = [_make_env(5, 1, EventType.CHARACTER_INTRODUCED, char_id)]
    ws_single = WorldState(
        series_id=EntityId(series_id),
        chapter=ChapterNumber(10),
        characters={
            char_id: CharacterState(
                character_id=EntityId(char_id), exists=True, alive=True
            )
        },
    )
    arc_single = engine.derive_character_arc(
        series_id=series_id,
        character_id=char_id,
        reader_chapter=10,
        envelopes=env_single,
        world_state=ws_single,
    )
    assert arc_single.start_chapter == 5
    assert arc_single.end_chapter == 5
    assert len(arc_single.milestones) == 1
    assert len(arc_single.turning_points) == 0
    # Single phase spanning Ch 5 to 10
    assert len(arc_single.phases) == 1
    assert arc_single.phases[0].from_chapter == 5
    assert arc_single.phases[0].to_chapter == 10
    assert arc_single.trajectory.current_status == "alive"
