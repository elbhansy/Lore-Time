from packages.domain.extraction.extraction_result import (
    ExtractionResult,
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.extractor import Extractor
from packages.domain.extraction.fact_type import FactType
from packages.domain.extraction.llm_provider import LLMProvider


class LLMExtractor(Extractor):
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.system_prompt = "Extract facts in strict JSON format matching the schema."

    def extract(self, series_id: str, chapter_id: str, text: str) -> ExtractionResult:
        raw_output = self.provider.generate_structured(self.system_prompt, text)

        facts = []
        if "facts" in raw_output:
            for item in raw_output["facts"]:
                # Basic validation
                try:
                    fact = RawExtractedFact(
                        type=FactType(item["type"]),
                        subject_raw=item["subject_raw"],
                        target_raw=item.get("target_raw"),
                        payload=item.get("payload", {}),
                        extraction_confidence=float(item.get("confidence", 0.0)),
                        evidence=RawFactEvidence(
                            location=item.get("evidence", {}).get("location", "")
                        ),
                    )
                    facts.append(fact)
                except (ValueError, KeyError):
                    # Malformed output from LLM, skip or log
                    continue

        return ExtractionResult(facts=facts, extractor_name="LLM_EXTRACTION")
