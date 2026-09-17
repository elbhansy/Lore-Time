import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


class EventResponse(BaseModel):
    id: uuid.UUID
    chapter_number: int
    sequence: int
    type: str
    subject_type: str
    subject_id: uuid.UUID
    target_type: str | None = None
    target_id: uuid.UUID | None = None
    metadata: dict[str, Any] = {}

    # We explicitly exclude previous_state and new_state from the default response
    # to maintain fine-grained API control, unless specifically requested.

    model_config = ConfigDict(from_attributes=True)
