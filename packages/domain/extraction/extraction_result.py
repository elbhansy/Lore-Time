from dataclasses import dataclass

from packages.domain.extraction.fact_type import FactType


@dataclass
class RawFactEvidence:
    location: str


@dataclass
class RawExtractedFact:
    type: FactType
    subject_raw: str
    target_raw: str | None
    payload: dict
    extraction_confidence: float
    evidence: RawFactEvidence


@dataclass
class ExtractionResult:
    facts: list[RawExtractedFact]
    extractor_name: str
