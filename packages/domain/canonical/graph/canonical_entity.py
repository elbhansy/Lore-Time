from dataclasses import dataclass, field
from typing import Any


@dataclass
class CanonicalEntity:
    id: str
    series_id: str
    type: str  # e.g. CHARACTER, LOCATION, ORGANIZATION
    name: str  # display name / fallback name
    metadata: dict[str, Any] = field(default_factory=dict)
