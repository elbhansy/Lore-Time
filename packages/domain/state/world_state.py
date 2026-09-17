from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from packages.domain.factions.faction_relationship_state import FactionRelationshipState
from packages.domain.factions.faction_state import FactionState
from packages.domain.factions.leadership_state import LeadershipState
from packages.domain.factions.membership_state import MembershipState
from packages.domain.power.rank_transition import RankTransition
from packages.domain.skills.skill_relation import SkillRelation
from packages.domain.skills.skill_state import SkillState

from ..value_objects.chapter_number import ChapterNumber
from ..value_objects.entity_id import EntityId
from .character_state import CharacterState
from .power_state import PowerState
from .relationship_state import RelationshipMap, RelationshipState


@dataclass(frozen=True)
class WorldState:
    series_id: EntityId
    chapter: ChapterNumber
    characters: dict[EntityId, CharacterState] = field(default_factory=dict)
    factions: dict[EntityId, FactionState] = field(default_factory=dict)
    powers: dict[EntityId, PowerState] = field(default_factory=dict)
    relationships: dict[Any, RelationshipState] = field(default_factory=RelationshipMap)
    memberships: dict[tuple[EntityId, EntityId], list[MembershipState]] = field(
        default_factory=lambda: defaultdict(list)
    )
    leaderships: dict[EntityId, list[LeadershipState]] = field(
        default_factory=lambda: defaultdict(list)
    )
    faction_relationships: dict[tuple[str, str], list[FactionRelationshipState]] = (
        field(default_factory=lambda: defaultdict(list))
    )

    # Skills keyed by (character_id, skill_id) mapping to list of historical states
    skills: dict[tuple[str, str], list[SkillState]] = field(
        default_factory=lambda: defaultdict(list)
    )

    # Dynamic skill relations revealed by events
    skill_relations: dict[str, SkillRelation] = field(default_factory=dict)

    # Rank transitions keyed by (character_id, power_system_id)
    rank_transitions: dict[tuple[str, str], list[RankTransition]] = field(
        default_factory=lambda: defaultdict(list)
    )
