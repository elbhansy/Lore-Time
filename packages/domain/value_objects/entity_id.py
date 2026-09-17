import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class EntityId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> "EntityId":
        return cls(value=uuid.uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> "EntityId":
        try:
            return cls(value=uuid.UUID(id_str))
        except ValueError:
            raise ValueError(f"Invalid UUID string: {id_str}")

    def __str__(self) -> str:
        return str(self.value)
