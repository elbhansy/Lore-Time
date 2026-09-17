from dataclasses import dataclass
from enum import Enum


class ChangeType(str, Enum):
    INTRODUCED = "INTRODUCED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"


@dataclass(frozen=True)
class CharacterDiff:
    character_id: str
    change_type: ChangeType
    before_status: str | None = None
    after_status: str | None = None
