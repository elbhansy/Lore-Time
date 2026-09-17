import uuid

from pydantic import BaseModel, ConfigDict


class SeriesResponse(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    total_chapters: int

    model_config = ConfigDict(from_attributes=True)
