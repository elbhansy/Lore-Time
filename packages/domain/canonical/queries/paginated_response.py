from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PaginatedResponse(Generic[T]):
    items: list[T]
    page: int
    limit: int
    total: int
    has_next: bool
