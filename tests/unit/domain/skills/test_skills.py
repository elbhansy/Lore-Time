from packages.domain.entities.event import Event
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.skills.skill_intelligence import SkillIntelligence
from packages.domain.skills.skill_progression import SkillProgressionService
from packages.domain.skills.skill_relation import (
    SkillRelation,
    SkillRelationScope,
    SkillRelationType,
)
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


def test_skill_evolution_visibility():
    state = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(200))
    applier = EventApplier()

    # Static Rule
    static_relations = [
        SkillRelation(
            id="spark_to_fireball",
            source_skill_id="spark",
            target_skill_id="fireball",
            type=SkillRelationType.EVOLVED_FROM,
            scope=SkillRelationScope.UNIVERSAL,
            introduced_chapter=50,
        )
    ]

    # Event-revealed Rule
    e1 = _create_event(
        1,
        150,
        EventType.SKILL_RELATION_REVEALED,
        "fireball",
        new_state={"relation_type": "EVOLVED_FROM"},
        target_id="inferno",
    )
    applier.apply(state, EventEnvelope(e1, ChapterNumber(150)))

    # Test Visibility at Ch 40
    vis_40 = SkillIntelligence.get_visible_relations(state, 40, static_relations)
    assert len(vis_40) == 0

    # Test Visibility at Ch 100
    vis_100 = SkillIntelligence.get_visible_relations(state, 100, static_relations)
    assert len(vis_100) == 1
    assert vis_100[0].id == "spark_to_fireball"

    # Test Visibility at Ch 200
    vis_200 = SkillIntelligence.get_visible_relations(state, 200, static_relations)
    assert len(vis_200) == 2
    assert any(r.id == "spark_to_fireball" for r in vis_200)
    assert any(r.target_skill_id == "inferno" for r in vis_200)


def test_character_specific_evolution():
    state = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(200))
    applier = EventApplier()

    static_relations = [
        SkillRelation(
            id="fireball_to_dragon",
            source_skill_id="fireball",
            target_skill_id="dragon_flame",
            type=SkillRelationType.EVOLVED_FROM,
            scope=SkillRelationScope.CHARACTER_SPECIFIC,
            character_id="A",
            introduced_chapter=100,
        )
    ]

    e1 = _create_event(1, 10, EventType.SKILL_UNLOCKED, "A", target_id="fireball")
    e2 = _create_event(2, 20, EventType.SKILL_UNLOCKED, "B", target_id="fireball")

    applier.apply(state, EventEnvelope(e1, ChapterNumber(10)))
    applier.apply(state, EventEnvelope(e2, ChapterNumber(20)))

    prog_a = SkillProgressionService.get_progression(state, "A", 200, static_relations)
    assert len(prog_a["relations"]) == 1

    prog_b = SkillProgressionService.get_progression(state, "B", 200, static_relations)
    assert len(prog_b["relations"]) == 0
