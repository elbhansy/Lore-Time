from packages.domain.extraction.extraction_result import RawExtractedFact
from packages.domain.extraction.fact_type import FactType


class ConflictDetector:
    @staticmethod
    def detect_conflicts(facts: list[RawExtractedFact]) -> list[RawExtractedFact]:
        """
        Analyzes a list of deduped facts (from the same chapter) for logical contradictions.
        Returns the list of facts that are in CONFLICT.
        """
        conflicting_facts = []

        # We group facts by subject and type to find contradictions.
        # e.g., Same character, POWER_RANK_CHANGED, but different "to_rank" payloads.
        rank_changes_by_subject: dict[str, list[RawExtractedFact]] = {}

        for fact in facts:
            if fact.type == FactType.POWER_RANK_CHANGED:
                subj = fact.subject_raw.lower()
                if subj not in rank_changes_by_subject:
                    rank_changes_by_subject[subj] = []
                rank_changes_by_subject[subj].append(fact)

        for subj, subj_facts in rank_changes_by_subject.items():
            if len(subj_facts) > 1:
                # E.g. two rank changes for the same character in the same chapter.
                # If they have different targets (to_rank), it's a conflict.
                targets = set(
                    f.payload.get("to_rank")
                    for f in subj_facts
                    if isinstance(f.payload, dict)
                )
                if len(targets) > 1:
                    conflicting_facts.extend(subj_facts)

        return conflicting_facts
