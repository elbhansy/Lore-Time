from typing import Any

from pydantic import BaseModel


class SkillExplorerItemDTO(BaseModel):
    id: str
    name: str
    introduced_chapter: int
    active_users_count: int


class SkillProgressionDTO(BaseModel):
    active_skills: list[dict[str, Any]]
    relations: list[dict[str, Any]]


class SkillEvolutionDTO(BaseModel):
    skill_id: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
