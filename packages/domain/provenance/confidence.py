from dataclasses import dataclass


@dataclass
class Confidence:
    extraction_confidence: float
    resolution_confidence: float
    validation_confidence: float
    source_reliability: float

    def __post_init__(self):
        self._validate_bound(self.extraction_confidence, "extraction_confidence")
        self._validate_bound(self.resolution_confidence, "resolution_confidence")
        self._validate_bound(self.validation_confidence, "validation_confidence")
        self._validate_bound(self.source_reliability, "source_reliability")

    def _validate_bound(self, value: float, name: str):
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"{name} must be between 0.0 and 1.0")

    @property
    def final_confidence(self) -> float:
        # Deterministic domain calculation
        val = (
            self.extraction_confidence
            * self.resolution_confidence
            * self.validation_confidence
            * self.source_reliability
        )
        return max(0.0, min(1.0, val))

    def to_dict(self) -> dict:
        return {
            "extraction": round(self.extraction_confidence, 4),
            "resolution": round(self.resolution_confidence, 4),
            "validation": round(self.validation_confidence, 4),
            "source_reliability": round(self.source_reliability, 4),
            "final": round(self.final_confidence, 4),
        }
