from packages.domain.extraction.extraction_result import (
    ExtractionResult,
    RawExtractedFact,
)
from packages.domain.extraction.extractor import Extractor
from packages.domain.extraction.fact_fingerprint import FactFingerprint
from packages.domain.ingestion.alias_normalizer import AliasNormalizer


class HybridExtractor(Extractor):
    def __init__(self, extractors: list[Extractor]):
        self.extractors = extractors

    def extract(self, series_id: str, chapter_id: str, text: str) -> ExtractionResult:
        all_facts = []
        for ext in self.extractors:
            result = ext.extract(series_id, chapter_id, text)
            all_facts.extend(result.facts)

        # Deduplication phase
        deduped_facts: dict[str, RawExtractedFact] = {}

        for fact in all_facts:
            # Normalize strings just for fingerprinting (Entity Resolution handles actual mapping later)
            subject_norm = AliasNormalizer.normalize(fact.subject_raw)
            target_norm = (
                AliasNormalizer.normalize(fact.target_raw) if fact.target_raw else ""
            )

            fingerprint = FactFingerprint.generate(
                series_id=series_id,
                chapter_id=chapter_id,
                fact_type=fact.type.value,
                subject_raw_norm=subject_norm,
                target_raw_norm=target_norm,
                payload=fact.payload,
            )

            # Simple rule: first one wins for the evidence, or you could merge evidence.
            if fingerprint not in deduped_facts:
                deduped_facts[fingerprint] = fact

        return ExtractionResult(
            facts=list(deduped_facts.values()), extractor_name="HYBRID_EXTRACTION"
        )
