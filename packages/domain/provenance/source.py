from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SourceStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    ARCHIVED = "ARCHIVED"


class SourceType(str, Enum):
    OFFICIAL = "OFFICIAL"
    PUBLISHER = "PUBLISHER"
    FAN_TRANSLATION = "FAN_TRANSLATION"
    MANUAL = "MANUAL"
    OCR = "OCR"
    LLM_EXTRACTION = "LLM_EXTRACTION"


@dataclass
class Source:
    id: str
    series_id: str
    type: SourceType
    name: str
    uri: str | None
    version: str  # fallback to empty string if NULL conceptually
    status: SourceStatus
    created_at: datetime
