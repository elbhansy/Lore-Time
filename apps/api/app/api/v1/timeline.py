import uuid

from fastapi import APIRouter, Depends, Query

from ...application.timeline.get_timeline_events import GetTimelineEventsUseCase
from ...application.timeline.get_world_state import GetWorldStateUseCase
from ...dependencies.services import (
    get_timeline_events_use_case,
    get_world_state_use_case,
)
from ...schemas.event import EventResponse
from ...schemas.world_state import (
    CharacterStateResponse,
    RelationshipStateResponse,
    WorldStateResponse,
)

router = APIRouter(prefix="/series", tags=["Timeline"])


def map_world_state(world_state) -> WorldStateResponse:
    # Map CharacterState
    characters = {
        k.value: CharacterStateResponse(
            exists=v.exists,
            alive=v.alive,
            rank=v.rank,
            unlocked_skills={s.value for s in v.unlocked_skills},
            faction_id=v.faction_id.value if v.faction_id else None,
        )
        for k, v in world_state.characters.items()
    }

    # Map relationships
    relationships = [
        RelationshipStateResponse(
            subject_id=v.subject_id.value,
            target_id=v.target_id.value,
            relationship_type=v.relationship_type,
            active=v.active,
        )
        for _, v in world_state.relationships.items()
    ]

    return WorldStateResponse(
        series_id=world_state.series_id.value,
        chapter=world_state.chapter.value,
        characters=characters,
        factions={},  # Future mapping
        powers={},  # Future mapping
        relationships=relationships,
    )


@router.get("/{series_id}/world-state", response_model=WorldStateResponse)
def get_world_state(
    series_id: uuid.UUID,
    chapter: int = Query(..., ge=1, description="The reader's current chapter"),
    use_case: GetWorldStateUseCase = Depends(get_world_state_use_case),
):
    ws = use_case.execute(series_id, chapter)
    return map_world_state(ws)


@router.get("/{series_id}/timeline", response_model=list[EventResponse])
def get_timeline(
    series_id: uuid.UUID,
    reader_chapter: int = Query(
        ..., ge=1, description="The maximum chapter visible to the reader"
    ),
    from_chapter: int = Query(1, alias="from", ge=1, description="Start chapter"),
    to_chapter: int = Query(..., alias="to", ge=1, description="End chapter"),
    use_case: GetTimelineEventsUseCase = Depends(get_timeline_events_use_case),
):
    envelopes = use_case.execute(series_id, reader_chapter, from_chapter, to_chapter)

    responses = []
    for env in envelopes:
        e = env.event
        responses.append(
            EventResponse(
                id=e.id.value,
                chapter_number=env.chapter_number.value,
                sequence=e.sequence,
                type=e.type.value,
                subject_type=e.subject_type.value,
                subject_id=e.subject_id.value,
                target_type=e.target_type.value if e.target_type else None,
                target_id=e.target_id.value if e.target_id else None,
                metadata=e.metadata,
            )
        )
    return responses
