"""Narrative Phase Builder for Narrative Intelligence (Phase 5.1).

Constructs contiguous, non-overlapping narrative phases bounded by turning points and reader horizon.
"""

import uuid

from packages.domain.narrative.models import (
    ArcMilestone,
    NarrativePhase,
    TurningPoint,
)
from packages.domain.state.character_state import CharacterState
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.entity_id import EntityId


def _get_char_state(
    world_state: WorldState | None, char_id: str
) -> CharacterState | None:
    if not world_state:
        return None
    cs = world_state.characters.get(char_id)
    if cs:
        return cs
    try:
        return world_state.characters.get(EntityId(uuid.UUID(char_id)))
    except Exception:
        return None


class NarrativePhaseBuilder:
    """Builds contiguous NarrativePhase entities from ordered milestones and turning points."""

    @staticmethod
    def build_phases(
        character_id: str,
        start_chapter: int,
        reader_chapter: int,
        milestones: list[ArcMilestone],
        turning_points: list[TurningPoint],
        final_world_state: WorldState | None = None,
    ) -> list[NarrativePhase]:
        if not milestones and start_chapter > reader_chapter:
            return []

        # If no turning points exist, the character's entire span up to reader_chapter is a single phase
        if not turning_points:
            ms_ids = [m.milestone_id for m in milestones]
            final_char_state = _get_char_state(final_world_state, character_id)
            return [
                NarrativePhase(
                    phase_id=f"phase:{character_id}:1:{start_chapter}:{reader_chapter}",
                    character_id=character_id,
                    phase_number=1,
                    title=f"Phase 1: Initial Progression (Ch {start_chapter}–{reader_chapter})",
                    from_chapter=start_chapter,
                    to_chapter=reader_chapter,
                    milestone_ids=ms_ids,
                    turning_point_id=None,
                    dominant_faction=final_char_state.faction_id
                    if final_char_state
                    else None,
                    rank_at_phase_end=final_char_state.rank
                    if final_char_state
                    else None,
                    is_active_at_horizon=True,
                )
            ]

        # Break into phases bounded by turning points
        phases: list[NarrativePhase] = []
        cur_from = start_chapter
        phase_num = 1

        for i, tp in enumerate(turning_points):
            tp_ch = tp.chapter
            phase_to = tp_ch

            # Collect milestones within this phase: [cur_from, phase_to]
            phase_milestones = [
                m.milestone_id for m in milestones if cur_from <= m.chapter <= phase_to
            ]

            phase_rank = tp.resulting_state.get("rank") or tp.previous_state.get("rank")
            phase_faction = tp.resulting_state.get(
                "faction_id"
            ) or tp.previous_state.get("faction_id")

            phases.append(
                NarrativePhase(
                    phase_id=f"phase:{character_id}:{phase_num}:{cur_from}:{phase_to}",
                    character_id=character_id,
                    phase_number=phase_num,
                    title=f"Phase {phase_num}: Leading to {tp.turning_point_type.value} (Ch {cur_from}–{phase_to})",
                    from_chapter=cur_from,
                    to_chapter=phase_to,
                    milestone_ids=phase_milestones,
                    turning_point_id=tp.turning_point_id,
                    dominant_faction=phase_faction,
                    rank_at_phase_end=phase_rank,
                    is_active_at_horizon=(
                        phase_to == reader_chapter and i == len(turning_points) - 1
                    ),
                )
            )

            cur_from = phase_to + 1
            phase_num += 1

        # If there are chapters between the last turning point and reader_chapter, add the trailing phase
        if cur_from <= reader_chapter:
            trailing_milestones = [
                m.milestone_id
                for m in milestones
                if cur_from <= m.chapter <= reader_chapter
            ]
            final_char_state = _get_char_state(final_world_state, character_id)
            phases.append(
                NarrativePhase(
                    phase_id=f"phase:{character_id}:{phase_num}:{cur_from}:{reader_chapter}",
                    character_id=character_id,
                    phase_number=phase_num,
                    title=f"Phase {phase_num}: Current Horizon (Ch {cur_from}–{reader_chapter})",
                    from_chapter=cur_from,
                    to_chapter=reader_chapter,
                    milestone_ids=trailing_milestones,
                    turning_point_id=None,
                    dominant_faction=final_char_state.faction_id
                    if final_char_state
                    else None,
                    rank_at_phase_end=final_char_state.rank
                    if final_char_state
                    else None,
                    is_active_at_horizon=True,
                )
            )

        return phases
