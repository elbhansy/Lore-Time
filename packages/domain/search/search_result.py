from dataclasses import dataclass, field
from typing import Any

from packages.domain.search.search_type import SearchType


@dataclass
class SearchResult:
    id: str
    type: SearchType
    title: str
    description: str | None = None
    relevance: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
