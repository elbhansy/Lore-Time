from packages.domain.entities.chapter import Chapter
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId


def test_chapter_valid():
    series_id = EntityId.generate()
    c = Chapter(
        id=EntityId.generate(),
        series_id=series_id,
        number=ChapterNumber(10),
        title="The Beginning",
    )
    assert c.series_id == series_id
    assert int(c.number) == 10
