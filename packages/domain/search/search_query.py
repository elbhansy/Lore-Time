from dataclasses import dataclass

from packages.domain.search.search_type import SearchType


@dataclass
class SearchQuery:
    text: str
    type: SearchType
    reader_chapter: int
    page: int = 1
    page_size: int = 20

    def __post_init__(self):
        if not self.text:
            raise ValueError("Search text cannot be empty.")
        if self.reader_chapter < 1:
            raise ValueError("Reader chapter must be >= 1.")
        if self.page < 1:
            raise ValueError("Page must be >= 1.")
        if self.page_size < 1 or self.page_size > 100:
            raise ValueError("Page size must be between 1 and 100.")
