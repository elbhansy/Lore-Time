from dataclasses import dataclass
from datetime import datetime

from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.evidence import Evidence


@dataclass
class Provenance:
    source_id: str
    evidence: Evidence
    confidence: Confidence
    captured_at: datetime

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "evidence": self.evidence.to_dict(),
            "confidence": self.confidence.to_dict(),
            "captured_at": self.captured_at.isoformat(),
        }
