import copy

from packages.domain.comparison.world_state_comparator import WorldStateComparator
from packages.domain.entities.event import Event
from packages.domain.impact.event_impact import EventImpact
from packages.domain.impact.impact_result import ImpactAnalysisResult
from packages.domain.impact.impact_type import ImpactType
from packages.domain.services.event_applier import EventApplier
from packages.domain.state.world_state import WorldState


class EventImpactAnalyzer:
    def __init__(self, event_applier: EventApplier):
        self.event_applier = event_applier

    def analyze(self, event: Event, before: WorldState) -> ImpactAnalysisResult:
        # We must clone 'before' state to apply the single event purely
        # In python, deepcopy is safe for our immutable/dataclass-based WorldState
        after = copy.deepcopy(before)

        # Apply the single event
        # EventApplier in our system currently takes WorldState and EventEnvelope
        # Since we just need to apply it, we pass it. The applier modifies state in-place.
        # However, our EventApplier might need chapter_number which comes from Envelope.
        # We can construct a mock envelope or use apply_event directly if modified.
        from packages.domain.services.event_ordering import EventEnvelope
        from packages.domain.value_objects.chapter_number import ChapterNumber

        env = EventEnvelope(
            event=event,
            chapter_number=ChapterNumber(
                event.metadata.get("chapter_number", before.chapter.value)
            ),
        )
        self.event_applier.apply(after, env)

        # Now compare deterministicly
        comp = WorldStateComparator.compare(before, after)

        impacts: list[EventImpact] = []
        event_id_str = str(event.id.value)
        ch_num = env.chapter_number.value
        e_type = event.type.value

        # 1. Character Changes
        for c in comp.character_changes:
            imp_type = (
                ImpactType.DIRECT
            )  # Simple heuristic for now: state changes from event are direct
            desc = f"CHARACTER_{c.change_type.value}"

            impacts.append(
                EventImpact(
                    event_id=event_id_str,
                    chapter_number=ch_num,
                    event_type=e_type,
                    impact_type=imp_type,
                    affected_entity_id=str(c.character_id),
                    description_key=desc,
                    details={"before": c.before_status, "after": c.after_status},
                )
            )

        # 2. Power Changes
        for p in comp.power_changes:
            impacts.append(
                EventImpact(
                    event_id=event_id_str,
                    chapter_number=ch_num,
                    event_type=e_type,
                    impact_type=ImpactType.DERIVED,
                    affected_entity_id=str(p.character_id),
                    description_key="POWER_CHANGED",
                    details={"before": p.before_rank, "after": p.after_rank},
                )
            )

        # 3. Relationship Changes
        for r in comp.relationship_changes:
            rel_id = f"{r.source_id}->{r.target_id}"
            impacts.append(
                EventImpact(
                    event_id=event_id_str,
                    chapter_number=ch_num,
                    event_type=e_type,
                    impact_type=ImpactType.DIRECT,
                    affected_entity_id=rel_id,
                    description_key=f"RELATIONSHIP_{r.change_type.value}",
                    details={"before": r.before_type, "after": r.after_type},
                )
            )

        # 4. Skill Changes
        for s in comp.skill_changes:
            impacts.append(
                EventImpact(
                    event_id=event_id_str,
                    chapter_number=ch_num,
                    event_type=e_type,
                    impact_type=ImpactType.DERIVED,
                    affected_entity_id=str(s.character_id),
                    description_key="SKILLS_UNLOCKED",
                    details={"unlocked": s.unlocked_skills},
                )
            )

        return ImpactAnalysisResult(
            event_id=event_id_str, chapter=ch_num, impacts=impacts
        )
