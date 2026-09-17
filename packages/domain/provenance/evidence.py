from dataclasses import dataclass


@dataclass
class Evidence:
    chapter_id: str
    location: str | None = None
    excerpt_hash: str | None = None

    def to_dict(self) -> dict:
        return {
            "chapter_id": self.chapter_id,
            "location": self.location,
            "excerpt_hash": self.excerpt_hash,
        }
