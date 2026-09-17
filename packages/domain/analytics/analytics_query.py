from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyticsQuery:
    """Scope for every analytics read. Unscoped queries are unrepresentable."""

    series_id: str
    from_chapter: int | None = None  # inclusive
    to_chapter: int | None = None  # inclusive
    page: int = 1
    limit: int = 50

    def __post_init__(self):
        if self.page < 1 or self.limit < 1:
            raise ValueError("pagination must be >= 1")
        if (
            self.from_chapter is not None
            and self.to_chapter is not None
            and self.from_chapter > self.to_chapter
        ):
            raise ValueError("from_chapter > to_chapter")
        # Chapter range bounds pagination offset math only when both set;
        # single-sided ranges are valid (e.g. "everything from chapter X").
