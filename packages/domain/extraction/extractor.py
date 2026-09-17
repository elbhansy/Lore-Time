from abc import ABC, abstractmethod

from packages.domain.extraction.extraction_result import ExtractionResult


class Extractor(ABC):
    @abstractmethod
    def extract(self, series_id: str, chapter_id: str, text: str) -> ExtractionResult:
        pass
