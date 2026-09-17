import logging

from packages.domain.entities.event import Event
from packages.domain.factions.faction_relationship_state import FactionRelationshipState
from packages.domain.factions.faction_state import FactionState
from packages.domain.factions.leadership_state import LeadershipState
from packages.domain.factions.membership_state import MembershipState
from packages.domain.power.rank_transition import RankTransition
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.skills.skill_relation import (
    SkillRelation,
    SkillRelationScope,
    SkillRelationType,
)
from packages.domain.skills.skill_state import SkillState
from packages.domain.state.character_state import CharacterState
from packages.domain.state.relationship_state import RelationshipState
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.event_type import EventType
from packages.domain.value_objects.relationship_type import RelationshipType

logger = logging.getLogger(__name__)


class EventApplier:
    def apply(self, state: WorldState, env: EventEnvelope | Event) -> None:
        """
        Mutates the internal dictionaries of WorldState.
        Unsupported events are logged and ignored without crashing.
        """
        if isinstance(env, EventEnvelope):
            event = env.event
            ch_num = env.chapter_number.value
        else:
            event = env
            ch_num = state.chapter.value

        match event.type:
            case EventType.CHARACTER_INTRODUCED:
                self._apply_character_introduced(state, event)
            case EventType.CHARACTER_DIED:
                self._apply_character_died(state, event)
            case EventType.POWER_RANK_CHANGED:
                self._apply_power_rank_changed(state, event, ch_num)
            case EventType.SKILL_UNLOCKED:
                self._apply_skill_unlocked(state, event, ch_num)
            case EventType.SKILL_UPGRADED:
                self._apply_skill_upgraded(state, event, ch_num)
            case EventType.SKILL_EVOLVED:
                self._apply_skill_evolved(state, event, ch_num)
            case EventType.SKILL_REPLACED:
                self._apply_skill_replaced(state, event, ch_num)
            case EventType.SKILL_COMBINED:
                self._apply_skill_combined(state, event, ch_num)
            case EventType.SKILL_LOST:
                self._apply_skill_lost(state, event, ch_num)
            case EventType.SKILL_RELATION_REVEALED:
                self._apply_skill_relation_revealed(state, event, ch_num)
            case EventType.RELATIONSHIP_CREATED:
                self._apply_relationship_created(state, event, ch_num)
            case EventType.RELATIONSHIP_CHANGED:
                self._apply_relationship_changed(state, event)
            case EventType.RELATIONSHIP_ENDED:
                self._apply_relationship_ended(state, event, ch_num)
            case EventType.FACTION_INTRODUCED:
                self._apply_faction_introduced(state, event)
            case EventType.FACTION_MEMBER_JOINED:
                self._apply_faction_member_joined(state, event, ch_num)
            case EventType.FACTION_MEMBER_LEFT:
                self._apply_faction_member_left(state, event, ch_num)
            case EventType.FACTION_LEADER_CHANGED:
                self._apply_faction_leader_changed(state, event, ch_num)
            case EventType.FACTION_RELATIONSHIP_CREATED:
                self._apply_faction_relationship_created(state, event, ch_num)
            case EventType.FACTION_RELATIONSHIP_CHANGED:
                self._apply_faction_relationship_changed(state, event)
            case EventType.FACTION_RELATIONSHIP_ENDED:
                self._apply_faction_relationship_ended(state, event, ch_num)
            case EventType.CUSTOM | EventType.LOCATION_DISCOVERED:
                logger.warning(
                    f"Event type {event.type.name} is currently unsupported and will be ignored."
                )
            case _:
                logger.warning(f"Unknown event type {event.type} encountered.")

    def _get_or_create_char(self, state: WorldState, char_id) -> CharacterState:
        if char_id not in state.characters:
            state.characters[char_id] = CharacterState(character_id=char_id)
        return state.characters[char_id]

    def _apply_character_introduced(self, state: WorldState, event: Event) -> None:
        char = self._get_or_create_char(state, event.subject_id)
        char.exists = True
        char.alive = True

    def _apply_character_died(self, state: WorldState, event: Event) -> None:
        char = self._get_or_create_char(state, event.subject_id)
        char.alive = False

    def _apply_power_rank_changed(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        char = self._get_or_create_char(state, event.subject_id)

        # M1.7: Support multiple power systems
        # fallback to 'default' if power_system_id not present in event
        sys_id = event.new_state.get("power_system_id", "default")
        new_rank = event.new_state.get("rank")
        if not new_rank:
            new_rank = event.new_state.get("rank_id")

        if new_rank:
            char.rank = new_rank

            char_id_str = str(event.subject_id)
            key = (char_id_str, sys_id)
            prev_rank = None
            if state.rank_transitions[key]:
                prev_rank = state.rank_transitions[key][-1].to_rank_id

            state.rank_transitions[key].append(
                RankTransition(
                    character_id=char_id_str,
                    power_system_id=sys_id,
                    from_rank_id=prev_rank,
                    to_rank_id=new_rank,
                    chapter=chapter_num,
                    event_id=str(event.id),
                )
            )

    def _apply_skill_unlocked(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        if not event.target_id:
            return
        char_id = event.subject_id
        skill_id = event.target_id
        key = (char_id, skill_id)

        self._get_or_create_char(state, char_id)

        state.skills[key].append(
            SkillState(
                character_id=char_id,
                skill_id=skill_id,
                active=True,
                unlocked_at=chapter_num,
            )
        )

        # update the snapshot
        state.characters[char_id].unlocked_skills.add(skill_id)

    def _apply_skill_upgraded(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        if not event.target_id:
            return
        char_id = event.subject_id
        skill_id = event.target_id
        key = (char_id, skill_id)

        if key in state.skills:
            for s in state.skills[key]:
                if s.active:
                    s.upgraded_at = chapter_num

    def _apply_skill_lost(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        if not event.target_id:
            return
        char_id = event.subject_id
        skill_id = event.target_id
        key = (char_id, skill_id)

        if key in state.skills:
            for s in state.skills[key]:
                if s.active:
                    s.active = False
                    s.lost_at = chapter_num

        if skill_id in state.characters[char_id].unlocked_skills:
            state.characters[char_id].unlocked_skills.remove(skill_id)

    def _apply_skill_evolved(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        # subject = character, target = new skill, new_state = {"from_skill_id": ...}
        if not event.target_id:
            return
        char_id = event.subject_id
        new_skill_id = event.target_id
        old_skill_id = event.new_state.get("from_skill_id")

        if old_skill_id:
            # Create a pseudo SKILL_LOST event for the old skill
            mock_lost = Event(
                id=event.id,
                series_id=event.series_id,
                chapter_id=event.chapter_id,
                sequence=event.sequence,
                type=EventType.SKILL_LOST,
                subject_type=event.subject_type,
                subject_id=char_id,
                target_id=old_skill_id,
            )
            self._apply_skill_lost(state, mock_lost, chapter_num)

        self._apply_skill_unlocked(state, event, chapter_num)

    def _apply_skill_replaced(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        self._apply_skill_evolved(state, event, chapter_num)

    def _apply_skill_combined(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        if not event.target_id:
            return
        char_id = event.subject_id
        new_skill_id = event.target_id
        old_skill_ids = event.new_state.get("from_skill_ids", [])

        for old_skill_id in old_skill_ids:
            mock_lost = Event(
                id=event.id,
                series_id=event.series_id,
                chapter_id=event.chapter_id,
                sequence=event.sequence,
                type=EventType.SKILL_LOST,
                subject_type=event.subject_type,
                subject_id=char_id,
                target_id=old_skill_id,
            )
            self._apply_skill_lost(state, mock_lost, chapter_num)

        self._apply_skill_unlocked(state, event, chapter_num)

    def _apply_skill_relation_revealed(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        # subject = source_skill, target = target_skill
        if not event.target_id:
            return
        source_id = str(event.subject_id)
        target_id = str(event.target_id)
        rel_type_str = event.new_state.get("relation_type", "UPGRADED_FROM")
        rel_type = SkillRelationType(rel_type_str)

        rel_id = f"{source_id}_{target_id}_{rel_type_str}"

        state.skill_relations[rel_id] = SkillRelation(
            id=rel_id,
            source_skill_id=source_id,
            target_skill_id=target_id,
            type=rel_type,
            scope=SkillRelationScope.UNIVERSAL,  # For events, we assume it's revealed universally unless specified otherwise, but actually event shouldn't define scope, it just reveals it.
            introduced_chapter=chapter_num,
        )

    def _apply_relationship_created(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        if not event.target_id:
            return
        rel_type_str = event.new_state.get("relationship_type", "OTHER")
        try:
            rel_type = RelationshipType(rel_type_str)
        except ValueError:
            rel_type = RelationshipType.OTHER

        key = (str(event.subject_id), str(event.target_id))
        state.relationships[key] = RelationshipState(
            subject_id=event.subject_id,
            target_id=event.target_id,
            relationship_type=rel_type,
            active=True,
            started_at=chapter_num,
        )

    def _apply_relationship_changed(self, state: WorldState, event: Event) -> None:
        if not event.target_id:
            return
        key = (str(event.subject_id), str(event.target_id))
        if key in state.relationships:
            new_type_str = event.new_state.get("relationship_type")
            if new_type_str:
                try:
                    rel_type = RelationshipType(new_type_str)
                    state.relationships[key].relationship_type = rel_type
                except ValueError:
                    pass

    def _apply_relationship_ended(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        if not event.target_id:
            return
        key = (str(event.subject_id), str(event.target_id))
        if key in state.relationships:
            state.relationships[key].active = False
            state.relationships[key].ended_at = chapter_num

    def _get_or_create_faction(
        self, state: WorldState, faction_id: str
    ) -> FactionState:
        if faction_id not in state.factions:
            state.factions[faction_id] = FactionState(faction_id=faction_id)
        return state.factions[faction_id]

    def _apply_faction_introduced(self, state: WorldState, event: Event) -> None:
        faction = self._get_or_create_faction(state, event.subject_id)
        faction.exists = True

    def _apply_faction_member_joined(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        if not event.target_id:
            return
        # subject = character, target = faction
        char_id = str(event.subject_id)
        faction_id = str(event.target_id)
        key = (char_id, faction_id)

        # Ensure existence in state
        self._get_or_create_char(state, event.subject_id)
        self._get_or_create_faction(state, event.target_id)

        state.memberships[key].append(
            MembershipState(
                character_id=char_id,
                faction_id=faction_id,
                active=True,
                joined_at=chapter_num,
            )
        )

    def _apply_faction_member_left(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        if not event.target_id:
            return
        char_id = str(event.subject_id)
        faction_id = str(event.target_id)
        key = (char_id, faction_id)

        # Find the active membership and end it
        if key in state.memberships:
            for ms in state.memberships[key]:
                if ms.active:
                    ms.active = False
                    ms.left_at = chapter_num

    def _apply_faction_leader_changed(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        # subject = faction, new_state = {"new_leader_id": "...", "previous_leader_id": "..."}
        faction_id = str(event.subject_id)
        new_leader_id = event.new_state.get("new_leader_id")
        if new_leader_id:
            new_leader_id = str(new_leader_id)

        # End current active leadership
        if faction_id in state.leaderships:
            for ls in state.leaderships[faction_id]:
                if ls.active:
                    ls.active = False
                    ls.ended_at = chapter_num

        # Start new leadership
        if new_leader_id:
            state.leaderships[faction_id].append(
                LeadershipState(
                    faction_id=faction_id,
                    leader_id=new_leader_id,
                    active=True,
                    started_at=chapter_num,
                )
            )

    def _apply_faction_relationship_created(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        if not event.target_id:
            return
        # subject = faction1, target = faction2
        rel_type = event.new_state.get("relationship_type", "OTHER")
        key = (event.subject_id, event.target_id)

        state.faction_relationships[key].append(
            FactionRelationshipState(
                subject_faction_id=event.subject_id,
                target_faction_id=event.target_id,
                relationship_type=rel_type,
                active=True,
                started_at=chapter_num,
            )
        )

    def _apply_faction_relationship_changed(
        self, state: WorldState, event: Event
    ) -> None:
        if not event.target_id:
            return
        key = (event.subject_id, event.target_id)
        new_type = event.new_state.get("relationship_type")
        if new_type and key in state.faction_relationships:
            for fr in state.faction_relationships[key]:
                if fr.active:
                    fr.relationship_type = new_type

    def _apply_faction_relationship_ended(
        self, state: WorldState, event: Event, chapter_num: int
    ) -> None:
        if not event.target_id:
            return
        key = (event.subject_id, event.target_id)
        if key in state.faction_relationships:
            for fr in state.faction_relationships[key]:
                if fr.active:
                    fr.active = False
                    fr.ended_at = chapter_num
