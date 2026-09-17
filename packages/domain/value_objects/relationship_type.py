from enum import Enum


class RelationshipType(str, Enum):
    ALLY = "ALLY"
    ENEMY = "ENEMY"
    FRIEND = "FRIEND"
    RIVAL = "RIVAL"
    FAMILY = "FAMILY"
    MASTER = "MASTER"
    DISCIPLE = "DISCIPLE"
    MEMBER = "MEMBER"
    LEADER = "LEADER"
    OTHER = "OTHER"
