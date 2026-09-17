import uuid

import pytest

from apps.api.app.application.comparison.compare_world_states import (
    CompareWorldStatesUseCase,
)
from apps.api.app.application.exceptions import InvalidChapter
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId


class MockWorldStateUseCase:
    def execute(self, series_id, chapter):
        # Return empty mock world state just for testing bounds
        from packages.domain.state.world_state import WorldState

        return WorldState(
            series_id=EntityId(str(series_id)), chapter=ChapterNumber(chapter)
        )


def test_compare_world_states_validation():
    uc = CompareWorldStatesUseCase(MockWorldStateUseCase())
    series_id = uuid.uuid4()

    # 1. from < to <= reader_chapter (Valid)
    uc.execute(series_id, 50, 100, 150)

    # 2. to > reader_chapter (Invalid, Spoiler)
    with pytest.raises(InvalidChapter, match="cannot exceed reader_chapter"):
        uc.execute(series_id, 50, 150, 100)

    # 3. from >= to (Invalid)
    with pytest.raises(InvalidChapter, match="strictly less than to_chapter"):
        uc.execute(series_id, 100, 50, 150)

    with pytest.raises(InvalidChapter, match="strictly less than to_chapter"):
        uc.execute(series_id, 50, 50, 150)

    # 4. from < 1 (Invalid)
    with pytest.raises(InvalidChapter, match="from_chapter must be positive"):
        uc.execute(series_id, 0, 50, 100)
