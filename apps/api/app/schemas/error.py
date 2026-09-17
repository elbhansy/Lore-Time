"""Standardized API Error Models."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    error: ErrorDetail

    # Maintain backward compatibility with clients expecting {"detail": ...}
    @property
    def detail(self) -> str:
        return self.error.message

    model_config = ConfigDict(from_attributes=True)
