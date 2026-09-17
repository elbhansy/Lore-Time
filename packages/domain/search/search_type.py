from enum import Enum


class SearchType(str, Enum):
    ALL = "ALL"
    CHARACTER = "CHARACTER"
    FACTION = "FACTION"
    POWER_SYSTEM = "POWER_SYSTEM"
    RANK = "RANK"
    SKILL = "SKILL"
    EVENT = "EVENT"
