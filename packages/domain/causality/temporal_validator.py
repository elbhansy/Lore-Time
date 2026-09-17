"""Temporal and Series Causal Validator (Phase 5.2 Milestone 5.2.4).

Ensures:
1. Temporal Validity: source_chapter <= target_chapter (no retrocausality).
   If source_chapter == target_chapter, source sequence < target sequence or source_id != target_id.
2. Series Isolation: source series == target series.
3. Temporal Scope / Horizon: source_chapter <= reader_chapter and target_chapter <= reader_chapter.
"""

from packages.domain.causality.exceptions import (
    CrossSeriesCausalityError,
    InvalidTemporalCausalityError,
)
from packages.domain.causality.models import CausalRelation


class TemporalCausalValidator:
    """Validates temporal ordering and tenant boundaries for causal relations."""

    @staticmethod
    def validate_relation(
        relation: CausalRelation,
        reader_chapter: int | None = None,
    ) -> None:
        """Validates a single causal relation against temporal and tenant constraints."""
        # 1. Temporal Ordering
        if relation.source_chapter > relation.target_chapter:
            raise InvalidTemporalCausalityError(
                f"Retrocausal edge detected: source event {relation.source_event_id} at ch "
                f"{relation.source_chapter} occurs after target event {relation.target_event_id} "
                f"at ch {relation.target_chapter}"
            )

        # Disallow self-causation
        if (
            relation.source_event_id == relation.target_event_id
            and relation.source_chapter == relation.target_chapter
        ):
            raise InvalidTemporalCausalityError(
                f"Self-causal loop detected: event {relation.source_event_id} cannot cause itself"
            )

        # 2. Reader Chapter Temporal Firewall
        if reader_chapter is not None:
            if relation.source_chapter > reader_chapter:
                raise InvalidTemporalCausalityError(
                    f"Temporal Firewall Violation: source event {relation.source_event_id} ch "
                    f"{relation.source_chapter} > readerChapter {reader_chapter}"
                )
            if relation.target_chapter > reader_chapter:
                raise InvalidTemporalCausalityError(
                    f"Temporal Firewall Violation: target event {relation.target_event_id} ch "
                    f"{relation.target_chapter} > readerChapter {reader_chapter}"
                )

    @staticmethod
    def validate_series_isolation(
        source_series_id: str,
        target_series_id: str,
    ) -> None:
        if str(source_series_id) != str(target_series_id):
            raise CrossSeriesCausalityError(
                f"Cross-series causality violation: source series {source_series_id} != "
                f"target series {target_series_id}"
            )
