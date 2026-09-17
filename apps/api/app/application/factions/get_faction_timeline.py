import uuid
from typing import Any, Protocol


class TimelineBackend(Protocol):
    def execute(self, series_id: uuid.UUID, chapter: int) -> list[dict[str, Any]]: ...


class GetFactionTimelineUseCase:
    def __init__(self, get_timeline_uc: TimelineBackend):
        self.get_timeline_uc = get_timeline_uc

    def execute(
        self, series_id: uuid.UUID, faction_id: str, chapter: int
    ) -> list[dict[str, Any]]:
        # Get full valid timeline up to chapter
        timeline = self.get_timeline_uc.execute(series_id, chapter)

        # Filter for events involving the faction directly
        faction_timeline = []
        for event in timeline:
            if event["subject_id"] == faction_id or event["target_id"] == faction_id:
                faction_timeline.append(event)

        return faction_timeline
