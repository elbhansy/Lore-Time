"""Character Arc Builder for Narrative Intelligence (Phase 5.1).

Assembles the full CharacterArc aggregate from canonical events and WorldState snapshots.
"""

import uuid

from packages.domain.narrative.milestone_extractor import MilestoneExtractor
from packages.domain.narrative.models import (
    ArcTrajectorySummary,
    CharacterArc,
    SignificanceLevel,
)
from packages.domain.narrative.narrative_phase_builder import NarrativePhaseBuilder
from packages.domain.narrative.turning_point_detector import TurningPointDetector
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.entity_id import EntityId


class CharacterArcBuilder:
    """Orchestrates extraction of milestones, detection of turning points,

    and construction of narrative phases into an immutable CharacterArc aggregate.
    """

    @classmethod
    def build_arc(
        cls,
        series_id: str,
        character_id: str,
        reader_chapter: int,
        envelopes: list[EventEnvelope],
        world_state: WorldState | None = None,
    ) -> CharacterArc:
        # 1. Temporal Firewall: Exclude all events beyond reader_chapter
        visible_envelopes = [
            env for env in envelopes if env.chapter_number.value <= reader_chapter
        ]

        # 2. Extract discrete milestones
        milestones = MilestoneExtractor.extract_milestones(
            character_id, visible_envelopes
        )

        # 3. Detect turning points
        turning_points = TurningPointDetector.detect_turning_points(
            character_id, milestones
        )

        # 4. Determine temporal boundaries
        if milestones:
            start_chapter = milestones[0].chapter
            end_chapter = min(max(m.chapter for m in milestones), reader_chapter)
        else:
            start_chapter = None
            end_chapter = None

        # 5. Build narrative phases
        if start_chapter is not None:
            phases = NarrativePhaseBuilder.build_phases(
                character_id=character_id,
                start_chapter=start_chapter,
                reader_chapter=reader_chapter,
                milestones=milestones,
                turning_points=turning_points,
                final_world_state=world_state,
            )
        else:
            phases = []

        # 6. Calculate trajectory summary
        char_state = None
        if world_state:
            char_state = world_state.characters.get(character_id)
            if not char_state:
                try:
                    char_state = world_state.characters.get(
                        EntityId(uuid.UUID(character_id))
                    )
                except Exception:
                    pass

        if char_state:
            if not char_state.exists:
                status = "unintroduced"
            elif not char_state.alive:
                status = "dead"
            else:
                status = "alive"
            cur_rank = char_state.rank
            cur_faction = char_state.faction_id
            skills_count = len(char_state.unlocked_skills)
        else:
            status = "unintroduced"
            cur_rank = None
            cur_faction = None
            skills_count = 0

        # Count relationships active in world_state for this character
        rel_count = 0
        if world_state:
            for (s_id, t_id), r_state in world_state.relationships.items():
                s_str = str(s_id.value if hasattr(s_id, "value") else s_id)
                t_str = str(t_id.value if hasattr(t_id, "value") else t_id)
                if (s_str == character_id or t_str == character_id) and r_state.active:
                    rel_count += 1

        # Highest significance level observed
        if any(tp.significance == SignificanceLevel.CRITICAL for tp in turning_points):
            highest_sig = SignificanceLevel.CRITICAL
        elif any(tp.significance == SignificanceLevel.HIGH for tp in turning_points):
            highest_sig = SignificanceLevel.HIGH
        elif any(tp.significance == SignificanceLevel.MEDIUM for tp in turning_points):
            highest_sig = SignificanceLevel.MEDIUM
        elif turning_points or milestones:
            highest_sig = SignificanceLevel.LOW
        else:
            highest_sig = SignificanceLevel.LOW

        trajectory = ArcTrajectorySummary(
            total_milestones=len(milestones),
            total_turning_points=len(turning_points),
            total_phases=len(phases),
            current_status=status,
            current_rank=cur_rank,
            current_faction=cur_faction,
            total_skills_unlocked=skills_count,
            total_relationships=rel_count,
            highest_significance=highest_sig,
        )

        return CharacterArc(
            series_id=series_id,
            character_id=character_id,
            reader_chapter=reader_chapter,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            milestones=milestones,
            turning_points=turning_points,
            phases=phases,
            trajectory=trajectory,
        )
