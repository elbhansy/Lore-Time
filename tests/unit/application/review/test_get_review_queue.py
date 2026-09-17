# Mock components to test application layer spoiler logic
class MockReviewItem:
    def __init__(self, id: str, chapter_num: int):
        self.id = id
        self.chapter_num = chapter_num


class MockReviewRepository:
    def __init__(self, items: list[MockReviewItem]):
        self.items = items

    def get_queue(self, series_id: str, reader_chapter: int) -> list[MockReviewItem]:
        # Implementation mimicking DB filtering
        return [item for item in self.items if item.chapter_num <= reader_chapter]


def test_get_review_queue_spoiler_firewall():
    items = [
        MockReviewItem("1", 10),
        MockReviewItem("2", 100),
        MockReviewItem("3", 101),
        MockReviewItem("4", 200),
    ]
    repo = MockReviewRepository(items)

    # Reader is at chapter 100
    queue = repo.get_queue("series_1", reader_chapter=100)

    # Must only contain items <= 100
    assert len(queue) == 2
    assert any(i.id == "1" for i in queue)
    assert any(i.id == "2" for i in queue)
    assert not any(i.id == "3" for i in queue)
    assert not any(i.id == "4" for i in queue)
