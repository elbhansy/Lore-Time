"""Turning Point Detector for Narrative Intelligence (Phase 5.1).

Identifies inflection points where character trajectory undergoes significant structural change:
- Mortality shifts (Death, Resurrection) -> CRITICAL
- Faction Realignment (Leadership, Defection) -> HIGH
- Power Breakthroughs (Rank change) -> HIGH
- Major Relationship Inversions (Ally <-> Enemy) -> HIGH
- Clustered Milestones (Multi-dimensional simultaneous change) -> HIGH
"""

from packages.domain.narrative.models import (
    ArcMilestone,
    MilestoneType,
    SignificanceLevel,
    TurningPoint,
    TurningPointType,
)


class TurningPointDetector:
    """Detects analytical turning points from a chronologically ordered list of ArcMilestones."""

    @staticmethod
    def detect_turning_points(
        character_id: str, milestones: list[ArcMilestone]
    ) -> list[TurningPoint]:
        turning_points: list[TurningPoint] = []

        # 1. Group milestones by chapter to evaluate single-chapter multi-dimensional shifts
        chapter_groups: dict[int, list[ArcMilestone]] = {}
        for m in milestones:
            chapter_groups.setdefault(m.chapter, []).append(m)

        for ch, m_list in sorted(chapter_groups.items()):
            # Sort chapter milestones deterministically
            m_list_sorted = sorted(m_list, key=lambda m: (m.sequence, m.milestone_id))

            # Check for Multi-Dimensional Shift in a single chapter (e.g. death + faction lost + rank lost)
            distinct_types = {m.milestone_type for m in m_list_sorted}
            if len(distinct_types) >= 2 and not any(
                m.milestone_type == MilestoneType.FIRST_APPEARANCE
                for m in m_list_sorted
            ):
                primary = m_list_sorted[0]
                dims = [m.milestone_type.value for m in m_list_sorted]
                turning_points.append(
                    TurningPoint(
                        turning_point_id=f"tp:{ch}:{primary.sequence}:{primary.event_id}:multi",
                        character_id=character_id,
                        chapter=ch,
                        sequence=primary.sequence,
                        event_id=primary.event_id,
                        turning_point_type=TurningPointType.MULTI_DIMENSIONAL_SHIFT,
                        significance=SignificanceLevel.HIGH,
                        description=f"Multi-dimensional turning point across {len(m_list_sorted)} milestones in Chapter {ch}.",
                        affected_dimensions=dims,
                        previous_state=primary.previous_state,
                        resulting_state=m_list_sorted[-1].new_state,
                    )
                )
                continue  # Processed group as compound turning point

            # Evaluate individual milestones for primary turning points
            for m in m_list_sorted:
                tp: TurningPoint | None = None

                match m.milestone_type:
                    case MilestoneType.DEATH:
                        tp = TurningPoint(
                            turning_point_id=f"tp:{m.chapter}:{m.sequence}:{m.event_id}:death",
                            character_id=character_id,
                            chapter=m.chapter,
                            sequence=m.sequence,
                            event_id=m.event_id,
                            turning_point_type=TurningPointType.MORTALITY_EVENT,
                            significance=SignificanceLevel.CRITICAL,
                            description=f"Critical mortality turning point: character died in Chapter {m.chapter}.",
                            affected_dimensions=["alive", "status"],
                            previous_state=m.previous_state,
                            resulting_state=m.new_state,
                        )

                    case MilestoneType.RESURRECTION:
                        tp = TurningPoint(
                            turning_point_id=f"tp:{m.chapter}:{m.sequence}:{m.event_id}:resurrect",
                            character_id=character_id,
                            chapter=m.chapter,
                            sequence=m.sequence,
                            event_id=m.event_id,
                            turning_point_type=TurningPointType.MORTALITY_EVENT,
                            significance=SignificanceLevel.CRITICAL,
                            description=f"Critical mortality turning point: character resurrected in Chapter {m.chapter}.",
                            affected_dimensions=["alive", "status"],
                            previous_state=m.previous_state,
                            resulting_state=m.new_state,
                        )

                    case MilestoneType.RANK_CHANGE:
                        tp = TurningPoint(
                            turning_point_id=f"tp:{m.chapter}:{m.sequence}:{m.event_id}:rank",
                            character_id=character_id,
                            chapter=m.chapter,
                            sequence=m.sequence,
                            event_id=m.event_id,
                            turning_point_type=TurningPointType.POWER_BREAKTHROUGH,
                            significance=SignificanceLevel.HIGH,
                            description=f"Power breakthrough: {m.description}",
                            affected_dimensions=["rank", "power"],
                            previous_state=m.previous_state,
                            resulting_state=m.new_state,
                        )

                    case MilestoneType.FACTION_LEADERSHIP | MilestoneType.FACTION_LEFT:
                        tp = TurningPoint(
                            turning_point_id=f"tp:{m.chapter}:{m.sequence}:{m.event_id}:faction",
                            character_id=character_id,
                            chapter=m.chapter,
                            sequence=m.sequence,
                            event_id=m.event_id,
                            turning_point_type=TurningPointType.FACTION_REALIGNMENT,
                            significance=SignificanceLevel.HIGH,
                            description=f"Faction realignment: {m.description}",
                            affected_dimensions=["faction_id", "affiliation"],
                            previous_state=m.previous_state,
                            resulting_state=m.new_state,
                        )

                    case MilestoneType.RELATIONSHIP_CHANGED:
                        prev = m.previous_state.get("type", "")
                        curr = m.new_state.get("type", "")
                        # Significant if polarity reversed (e.g. ally <-> enemy)
                        if ("ally" in prev and "enemy" in curr) or (
                            "enemy" in prev and "ally" in curr
                        ):
                            tp = TurningPoint(
                                turning_point_id=f"tp:{m.chapter}:{m.sequence}:{m.event_id}:rel_inversion",
                                character_id=character_id,
                                chapter=m.chapter,
                                sequence=m.sequence,
                                event_id=m.event_id,
                                turning_point_type=TurningPointType.RELATIONSHIP_TRANSFORMATION,
                                significance=SignificanceLevel.HIGH,
                                description=f"Relationship transformation: inverted from {prev} to {curr}.",
                                affected_dimensions=["relationship", "allegiance"],
                                previous_state=m.previous_state,
                                resulting_state=m.new_state,
                            )

                if tp:
                    turning_points.append(tp)

        # Deterministic sort: chapter ASC, sequence ASC, turning_point_id ASC
        return sorted(
            turning_points, key=lambda t: (t.chapter, t.sequence, t.turning_point_id)
        )
