from dataclasses import dataclass


@dataclass(frozen=True)
class ChapterNumber:
    value: int

    def __post_init__(self):
        if not isinstance(self.value, int):
            raise TypeError("Chapter number must be an integer.")
        if self.value < 1:
            raise ValueError("Chapter number must be 1 or greater.")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: "ChapterNumber") -> bool:
        if not isinstance(other, ChapterNumber):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: "ChapterNumber") -> bool:
        if not isinstance(other, ChapterNumber):
            return NotImplemented
        return self.value <= other.value
