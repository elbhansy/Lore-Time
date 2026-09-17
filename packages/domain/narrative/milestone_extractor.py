"""Milestone Extractor for Character Arc derivation (Phase 5.1).

Extracts canonical ArcMilestones from sorted EventEnvelopes associated with a target character.
"""

from packages.domain.entities.event import Event
from packages.domain.narrative.models import ArcMilestone, MilestoneType
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.value_objects.event_type import EventType


class MilestoneExtractor:
    """Extracts discrete ArcMilestones from canonical events for a character."""

    @staticmethod
    def extract_milestones(
        character_id: str, envelopes: list[EventEnvelope]
    ) -> list[ArcMilestone]:
        milestones: list[ArcMilestone] = []

        for env in envelopes:
            event: Event = env.event
            ch_num = env.chapter_number.value
            seq = event.sequence
            eid_str = str(event.id.value)
            subj_id = str(event.subject_id.value)
            tgt_id = str(event.target_id.value) if event.target_id else None

            # Only consider events where the character is either subject or target
            if subj_id != character_id and tgt_id != character_id:
                continue

            milestone: ArcMilestone | None = None

            match event.type:
                case EventType.CHARACTER_INTRODUCED:
                    if subj_id == character_id:
                        milestone = ArcMilestone(
                            milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:intro",
                            character_id=character_id,
                            chapter=ch_num,
                            sequence=seq,
                            event_id=eid_str,
                            milestone_type=MilestoneType.FIRST_APPEARANCE,
                            description=f"Character introduced into the narrative in Chapter {ch_num}.",
                            previous_state=event.previous_state,
                            new_state=event.new_state,
                        )

                case EventType.CHARACTER_DIED:
                    if subj_id == character_id:
                        milestone = ArcMilestone(
                            milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:death",
                            character_id=character_id,
                            chapter=ch_num,
                            sequence=seq,
                            event_id=eid_str,
                            milestone_type=MilestoneType.DEATH,
                            description=f"Character died in Chapter {ch_num}.",
                            previous_state=event.previous_state,
                            new_state=event.new_state,
                        )

                case EventType.POWER_RANK_CHANGED:
                    if subj_id == character_id:
                        prev_rank = event.previous_state.get("rank")
                        new_rank = event.new_state.get("rank")
                        milestone = ArcMilestone(
                            milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:rank",
                            character_id=character_id,
                            chapter=ch_num,
                            sequence=seq,
                            event_id=eid_str,
                            milestone_type=MilestoneType.RANK_CHANGE,
                            description=f"Power rank changed from {prev_rank} to {new_rank}.",
                            previous_state=event.previous_state,
                            new_state=event.new_state,
                        )

                case EventType.SKILL_UNLOCKED:
                    if subj_id == character_id:
                        skill_name = event.metadata.get(
                            "skill_name"
                        ) or event.new_state.get("skill_id", "skill")
                        milestone = ArcMilestone(
                            milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:skill_unlock",
                            character_id=character_id,
                            chapter=ch_num,
                            sequence=seq,
                            event_id=eid_str,
                            milestone_type=MilestoneType.SKILL_ACQUIRED,
                            description=f"Unlocked new skill: {skill_name}.",
                            previous_state=event.previous_state,
                            new_state=event.new_state,
                        )

                case EventType.SKILL_EVOLVED | EventType.SKILL_UPGRADED:
                    if subj_id == character_id:
                        skill_name = event.metadata.get("skill_name") or "skill"
                        milestone = ArcMilestone(
                            milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:skill_evolve",
                            character_id=character_id,
                            chapter=ch_num,
                            sequence=seq,
                            event_id=eid_str,
                            milestone_type=MilestoneType.SKILL_EVOLVED,
                            description=f"Skill evolved/upgraded: {skill_name}.",
                            previous_state=event.previous_state,
                            new_state=event.new_state,
                        )

                case EventType.SKILL_LOST:
                    if subj_id == character_id:
                        skill_name = event.metadata.get("skill_name") or "skill"
                        milestone = ArcMilestone(
                            milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:skill_lost",
                            character_id=character_id,
                            chapter=ch_num,
                            sequence=seq,
                            event_id=eid_str,
                            milestone_type=MilestoneType.SKILL_LOST,
                            description=f"Lost skill: {skill_name}.",
                            previous_state=event.previous_state,
                            new_state=event.new_state,
                        )

                case EventType.FACTION_MEMBER_JOINED:
                    if subj_id == character_id:
                        fac_name = event.metadata.get(
                            "faction_name"
                        ) or event.new_state.get("faction_id", "faction")
                        milestone = ArcMilestone(
                            milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:faction_join",
                            character_id=character_id,
                            chapter=ch_num,
                            sequence=seq,
                            event_id=eid_str,
                            milestone_type=MilestoneType.FACTION_JOINED,
                            description=f"Joined faction: {fac_name}.",
                            previous_state=event.previous_state,
                            new_state=event.new_state,
                        )

                case EventType.FACTION_MEMBER_LEFT:
                    if subj_id == character_id:
                        fac_name = event.metadata.get(
                            "faction_name"
                        ) or event.previous_state.get("faction_id", "faction")
                        milestone = ArcMilestone(
                            milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:faction_left",
                            character_id=character_id,
                            chapter=ch_num,
                            sequence=seq,
                            event_id=eid_str,
                            milestone_type=MilestoneType.FACTION_LEFT,
                            description=f"Departed from faction: {fac_name}.",
                            previous_state=event.previous_state,
                            new_state=event.new_state,
                        )

                case EventType.FACTION_LEADER_CHANGED:
                    if (
                        subj_id == character_id
                        or event.new_state.get("leader_id") == character_id
                    ):
                        fac_name = event.metadata.get("faction_name") or "faction"
                        milestone = ArcMilestone(
                            milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:faction_leader",
                            character_id=character_id,
                            chapter=ch_num,
                            sequence=seq,
                            event_id=eid_str,
                            milestone_type=MilestoneType.FACTION_LEADERSHIP,
                            description=f"Assumed leadership of faction: {fac_name}.",
                            previous_state=event.previous_state,
                            new_state=event.new_state,
                        )

                case EventType.RELATIONSHIP_CREATED:
                    other_id = tgt_id if subj_id == character_id else subj_id
                    rel_type = event.new_state.get("type", "relation")
                    milestone = ArcMilestone(
                        milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:rel_created",
                        character_id=character_id,
                        chapter=ch_num,
                        sequence=seq,
                        event_id=eid_str,
                        milestone_type=MilestoneType.RELATIONSHIP_FORMED,
                        description=f"Formed {rel_type} relationship with entity {other_id[:8]}.",
                        previous_state=event.previous_state,
                        new_state=event.new_state,
                    )

                case EventType.RELATIONSHIP_CHANGED:
                    other_id = tgt_id if subj_id == character_id else subj_id
                    prev_type = event.previous_state.get("type", "relation")
                    new_type = event.new_state.get("type", "relation")
                    milestone = ArcMilestone(
                        milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:rel_changed",
                        character_id=character_id,
                        chapter=ch_num,
                        sequence=seq,
                        event_id=eid_str,
                        milestone_type=MilestoneType.RELATIONSHIP_CHANGED,
                        description=f"Relationship with entity {other_id[:8]} shifted from {prev_type} to {new_type}.",
                        previous_state=event.previous_state,
                        new_state=event.new_state,
                    )

                case EventType.RELATIONSHIP_ENDED:
                    other_id = tgt_id if subj_id == character_id else subj_id
                    milestone = ArcMilestone(
                        milestone_id=f"ms:{ch_num}:{seq}:{eid_str}:rel_ended",
                        character_id=character_id,
                        chapter=ch_num,
                        sequence=seq,
                        event_id=eid_str,
                        milestone_type=MilestoneType.RELATIONSHIP_SEVERED,
                        description=f"Relationship with entity {other_id[:8]} severed.",
                        previous_state=event.previous_state,
                        new_state=event.new_state,
                    )

            if milestone:
                milestones.append(milestone)

        # Explicit deterministic sort: chapter ASC, sequence ASC, milestone_id ASC
        return sorted(milestones, key=lambda m: (m.chapter, m.sequence, m.milestone_id))
