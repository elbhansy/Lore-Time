from datetime import datetime

import pytest

from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.source import Source, SourceStatus, SourceType


def test_confidence_deterministic_calculation():
    c = Confidence(
        extraction_confidence=0.9,
        resolution_confidence=0.8,
        validation_confidence=1.0,
        source_reliability=0.5,
    )
    # 0.9 * 0.8 * 1.0 * 0.5 = 0.36
    assert abs(c.final_confidence - 0.36) < 0.0001

    # Check max bound
    c_max = Confidence(1.0, 1.0, 1.0, 1.0)
    assert c_max.final_confidence == 1.0

    # Check min bound
    c_min = Confidence(0.0, 0.5, 0.5, 0.5)
    assert c_min.final_confidence == 0.0


def test_confidence_validation():
    with pytest.raises(
        ValueError, match="extraction_confidence must be between 0.0 and 1.0"
    ):
        Confidence(1.5, 1.0, 1.0, 1.0)

    with pytest.raises(
        ValueError, match="source_reliability must be between 0.0 and 1.0"
    ):
        Confidence(0.5, 0.5, 0.5, -0.1)


class MockSourceGovernance:
    def can_publish(self, source: Source) -> bool:
        return source.status == SourceStatus.ACTIVE


def test_source_governance_blocks_pending():
    gov = MockSourceGovernance()

    active_source = Source(
        "1",
        "s1",
        SourceType.MANUAL,
        "Manual",
        None,
        "",
        SourceStatus.ACTIVE,
        datetime.now(),
    )
    pending_source = Source(
        "2",
        "s1",
        SourceType.LLM_EXTRACTION,
        "LLM",
        None,
        "",
        SourceStatus.PENDING,
        datetime.now(),
    )
    disabled_source = Source(
        "3",
        "s1",
        SourceType.MANUAL,
        "Old",
        None,
        "",
        SourceStatus.DISABLED,
        datetime.now(),
    )

    assert gov.can_publish(active_source) is True
    assert gov.can_publish(pending_source) is False
    assert gov.can_publish(disabled_source) is False
