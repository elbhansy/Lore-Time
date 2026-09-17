import uuid

from fastapi import APIRouter, Depends, Query

from ...application.characters.get_character import GetCharacterUseCase
from ...application.characters.get_characters import GetCharactersUseCase
from ...dependencies.services import get_character_use_case, get_characters_use_case
from ...schemas.character import CharacterResponse, CharacterStateResponse

router = APIRouter(prefix="/series", tags=["Characters"])


@router.get("/{series_id}/characters", response_model=list[CharacterResponse])
def list_characters(
    series_id: uuid.UUID,
    use_case: GetCharactersUseCase = Depends(get_characters_use_case),
):
    characters = use_case.execute(series_id)
    # Return minimal details (without state, since list endpoint doesn't have reader_chapter)
    # Wait, the frontend needs the characters' names. We will return minimal info.
    # The CharacterResponse schema expects `state` and `as_of_chapter`.
    # Let's return them with a dummy state if needed, or better, we should have a `CharacterListResponse` schema.
    # But since Pydantic ignores extra fields, we can just return CharacterResponse with empty state.
    # To conform strictly to the schema, we must provide state.
    return [
        CharacterResponse(
            id=c.id.value,
            name=c.name,
            state=CharacterStateResponse(
                exists=False,
                alive=False,
                rank=None,
                unlocked_skills=set(),
                faction_id=None,
            ),
            as_of_chapter=0,
        )
        for c in characters
    ]


@router.get("/{series_id}/characters/{character_id}", response_model=CharacterResponse)
def get_character(
    series_id: uuid.UUID,
    character_id: uuid.UUID,
    chapter: int = Query(..., ge=1, description="The reader's current chapter"),
    use_case: GetCharacterUseCase = Depends(get_character_use_case),
):
    char_entity, char_state = use_case.execute(series_id, character_id, chapter)

    state_response = CharacterStateResponse(
        exists=char_state.exists,
        alive=char_state.alive,
        rank=char_state.rank,
        unlocked_skills={s.value for s in char_state.unlocked_skills},
        faction_id=char_state.faction_id.value if char_state.faction_id else None,
    )

    return CharacterResponse(
        id=char_entity.id.value,
        name=char_entity.name,
        state=state_response,
        as_of_chapter=chapter,
    )
