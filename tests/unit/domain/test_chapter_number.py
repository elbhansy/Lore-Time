import pytest

from packages.domain.value_objects.chapter_number import ChapterNumber


def test_chapter_number_valid():
    assert int(ChapterNumber(1)) == 1
    assert int(ChapterNumber(100)) == 100


def test_chapter_number_zero_invalid():
    with pytest.raises(ValueError):
        ChapterNumber(0)


def test_chapter_number_negative_invalid():
    with pytest.raises(ValueError):
        ChapterNumber(-1)


def test_chapter_number_float_invalid():
    with pytest.raises(TypeError):
        ChapterNumber(1.5)


def test_chapter_number_comparison():
    c1 = ChapterNumber(1)
    c100 = ChapterNumber(100)
    assert c1 < c100
    assert c1 <= c100
    assert c100 > c1
