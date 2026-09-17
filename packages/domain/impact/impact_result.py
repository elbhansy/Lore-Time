from dataclasses import dataclass

from .event_impact import EventImpact


@dataclass(frozen=True)
class ImpactAnalysisResult:
    event_id: str
    chapter: int
    impacts: list[EventImpact]

    @property
    def affected_entities(self) -> list[str]:
        return sorted(list(set(imp.affected_entity_id for imp in self.impacts)))
