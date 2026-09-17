import re

from packages.domain.extraction.extraction_result import (
    ExtractionResult,
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.extractor import Extractor
from packages.domain.extraction.fact_type import FactType


class RuleExtractor(Extractor):
    def extract(self, series_id: str, chapter_id: str, text: str) -> ExtractionResult:
        facts = []

        # Extremely basic rule: "Rank increased from B to A for Dokja"
        # This is just a placeholder pattern to prove the hybrid concept.
        pattern = re.compile(
            r"Rank increased from ([SABCDE]) to ([SABCDE]) for ([\w\s]+)", re.IGNORECASE
        )

        for i, line in enumerate(text.split("\n")):
            match = pattern.search(line)
            if match:
                from_rank, to_rank, subject_raw = match.groups()
                facts.append(
                    RawExtractedFact(
                        type=FactType.POWER_RANK_CHANGED,
                        subject_raw=subject_raw.strip(),
                        target_raw=None,
                        payload={
                            "from_rank": from_rank.upper(),
                            "to_rank": to_rank.upper(),
                        },
                        extraction_confidence=0.99,  # Rules have high confidence
                        evidence=RawFactEvidence(location=f"line:{i}"),
                    )
                )

        return ExtractionResult(facts=facts, extractor_name="RULE_EXTRACTION")
