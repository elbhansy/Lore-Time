from packages.domain.extraction.conflict_detector import ConflictDetector
from packages.domain.extraction.extraction_result import (
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.fact_type import FactType


def test_conflict_detection():
    f1 = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Dokja",
        target_raw=None,
        payload={"from_rank": "B", "to_rank": "A"},
        extraction_confidence=0.9,
        evidence=RawFactEvidence(location="p1"),
    )
    f2 = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Dokja",
        target_raw=None,
        payload={"from_rank": "B", "to_rank": "S"},
        extraction_confidence=0.95,
        evidence=RawFactEvidence(location="p2"),
    )

    # Same character, same type, but to_rank is different. Should conflict.
    conflicts = ConflictDetector.detect_conflicts([f1, f2])

    assert len(conflicts) == 2
    assert f1 in conflicts
    assert f2 in conflicts


def test_no_conflict():
    f1 = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Dokja",
        target_raw=None,
        payload={"from_rank": "B", "to_rank": "A"},
        extraction_confidence=0.9,
        evidence=RawFactEvidence(location="p1"),
    )
    f2 = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Joonghyuk",
        target_raw=None,
        payload={"from_rank": "A", "to_rank": "S"},
        extraction_confidence=0.95,
        evidence=RawFactEvidence(location="p2"),
    )

    # Different subjects -> no conflict
    conflicts = ConflictDetector.detect_conflicts([f1, f2])
    assert len(conflicts) == 0
