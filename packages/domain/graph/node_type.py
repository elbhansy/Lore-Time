from enum import Enum


class NodeType(str, Enum):
    CHARACTER = "CHARACTER"
    FACTION = "FACTION"
    POWER_SYSTEM = "POWER_SYSTEM"
    RANK = "RANK"
    SKILL = "SKILL"
