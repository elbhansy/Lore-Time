import uuid

from apps.api.app.schemas.relationship import (
    RelationshipHistoryEvent,
    RelationshipHistoryResponse,
)
from packages.domain.repositories.character_repository import CharacterRepository
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.services.event_ordering import sort_events
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.event_type import EventType

from ..exceptions import CharacterNotFound, InvalidChapter


class GetRelationshipHistoryUseCase:
    def __init__(
        self, event_repo: EventRepository, character_repo: CharacterRepository
    ):
        self.event_repo = event_repo
        self.character_repo = character_repo

    def execute(
        self,
        series_id: uuid.UUID,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        reader_chapter: int,
    ) -> RelationshipHistoryResponse:
        if reader_chapter < 1:
            raise InvalidChapter("Chapter must be positive")

        series_entity_id = EntityId(series_id)
        s_id = EntityId(source_id)
        t_id = EntityId(target_id)

        # Validate ownership
        source_char = self.character_repo.get(s_id)
        target_char = self.character_repo.get(t_id)

        if not source_char or source_char.series_id != series_entity_id:
            raise CharacterNotFound(
                f"Character {source_id} not found in series {series_id}"
            )

        if not target_char or target_char.series_id != series_entity_id:
            raise CharacterNotFound(
                f"Character {target_id} not found in series {series_id}"
            )

        # Fetch events for the series
        envelopes = self.event_repo.get_all_by_series(series_entity_id)

        # Spoiler Firewall: filter out events after reader_chapter
        envelopes = [
            env for env in envelopes if env.chapter_number.value <= reader_chapter
        ]
        envelopes = sort_events(envelopes)

        history = []
        for env in envelopes:
            event = env.event
            if event.type in (
                EventType.RELATIONSHIP_CREATED,
                EventType.RELATIONSHIP_CHANGED,
                EventType.RELATIONSHIP_ENDED,
            ):
                # Strict directionality
                if event.subject_id == s_id and event.target_id == t_id:
                    if event.type == EventType.RELATIONSHIP_ENDED:
                        type_val = "ENDED"
                    else:
                        type_val = event.new_state.get("relationship_type", "UNKNOWN")

                    history.append(
                        RelationshipHistoryEvent(
                            chapter=env.chapter_number.value, type=type_val
                        )
                    )

        return RelationshipHistoryResponse(
            source_id=str(source_id), target_id=str(target_id), history=history
        )
