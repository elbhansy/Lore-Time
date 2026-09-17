from dataclasses import dataclass

from ..value_objects.entity_id import EntityId
from ..value_objects.relationship_type import RelationshipType


@dataclass
class RelationshipState:
    subject_id: EntityId
    target_id: EntityId
    relationship_type: RelationshipType
    active: bool
    started_at: int
    ended_at: int | None = None


class RelationshipMap(dict):
    """
    Dictionary for relationships that supports lookup and indexing by either
    tuples of strings or tuples of EntityIds.
    """

    @staticmethod
    def _normalize_key(key):
        if isinstance(key, (tuple, list)) and len(key) == 2:
            return (str(key[0]), str(key[1]))
        return key

    def __getitem__(self, key):
        return super().__getitem__(self._normalize_key(key))

    def __setitem__(self, key, value):
        super().__setitem__(self._normalize_key(key), value)

    def __contains__(self, key):
        return super().__contains__(self._normalize_key(key))

    def get(self, key, default=None):
        return super().get(self._normalize_key(key), default)

    def pop(self, key, *args):
        return super().pop(self._normalize_key(key), *args)
