from infrastructure.extraction.providers.hybrid_extractor import HybridExtractor
from infrastructure.extraction.providers.llm_extractor import LLMExtractor
from infrastructure.extraction.providers.mock_llm_provider import MockLLMProvider
from infrastructure.extraction.providers.rule_extractor import RuleExtractor
from packages.domain.extraction.fact_fingerprint import FactFingerprint


def test_fact_fingerprint():
    # Identical facts should have same fingerprint regardless of confidence
    f1 = FactFingerprint.generate(
        "s1", "c1", "POWER_RANK_CHANGED", "dokja", "", {"from": "B", "to": "A"}
    )
    f2 = FactFingerprint.generate(
        "s1", "c1", "POWER_RANK_CHANGED", "dokja", "", {"from": "B", "to": "A"}
    )

    assert f1 == f2

    # Different payload -> different fingerprint
    f3 = FactFingerprint.generate(
        "s1", "c1", "POWER_RANK_CHANGED", "dokja", "", {"from": "B", "to": "C"}
    )
    assert f1 != f3


def test_hybrid_deduplication():
    # Mock LLM returns a fact
    mock_llm = MockLLMProvider()
    mock_llm.set_mock_response(
        {
            "facts": [
                {
                    "type": "POWER_RANK_CHANGED",
                    "subject_raw": "Dokja",
                    "payload": {"from_rank": "B", "to_rank": "A"},
                    "confidence": 0.8,
                    "evidence": {"location": "p42"},
                }
            ]
        }
    )

    llm_ext = LLMExtractor(mock_llm)
    rule_ext = RuleExtractor()

    text = "Rank increased from B to A for Dokja\nSome other text."

    hybrid = HybridExtractor([rule_ext, llm_ext])
    result = hybrid.extract("s1", "c1", text)

    # LLM found 1, Rule found 1. Both identical semantically.
    # Should deduplicate to 1.
    assert len(result.facts) == 1
    assert result.facts[0].subject_raw.lower() == "dokja"
