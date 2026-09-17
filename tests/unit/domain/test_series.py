import pytest

from packages.domain.entities.series import Series
from packages.domain.value_objects.entity_id import EntityId


def test_series_valid():
    s = Series(
        id=EntityId.generate(),
        title="Solo Leveling",
        slug="solo-leveling",
        total_chapters=200,
    )
    assert s.title == "Solo Leveling"
    assert s.slug == "solo-leveling"


def test_series_empty_title_invalid():
    with pytest.raises(ValueError):
        Series(id=EntityId.generate(), title="", slug="slug", total_chapters=10)
    with pytest.raises(ValueError):
        Series(id=EntityId.generate(), title="   ", slug="slug", total_chapters=10)


def test_series_empty_slug_invalid():
    with pytest.raises(ValueError):
        Series(id=EntityId.generate(), title="Title", slug="", total_chapters=10)


def test_series_negative_chapters_invalid():
    with pytest.raises(ValueError):
        Series(id=EntityId.generate(), title="Title", slug="slug", total_chapters=-1)
