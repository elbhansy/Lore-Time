import uuid
from typing import Any

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.services.power_progression import PowerProgressionService
from packages.domain.services.rank_comparison import RankComparisonService
from packages.domain.value_objects.entity_id import EntityId


class GetPowerProgressionUseCase:
    def __init__(
        self,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
    ):
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider

    def execute(
        self,
        series_id: uuid.UUID,
        character_id: str,
        power_system_id: str,
        chapter: int,
    ) -> dict[str, Any]:
        ws = self.get_world_state_uc.execute(series_id, chapter)
        entities = self.entities_provider.get_static_entities(EntityId(series_id))

        progression = PowerProgressionService.get_progression(
            ws, character_id, power_system_id, chapter
        )

        # Hydrate with rank details and detect breakthroughs
        hydrated_transitions = []
        for t in progression.transitions:
            from_rank = entities.ranks.get(t.from_rank_id) if t.from_rank_id else None
            to_rank = entities.ranks.get(t.to_rank_id) if t.to_rank_id else None

            # Check spoiler firewall on the ranks themselves (just in case they were introduced later)
            if (
                to_rank
                and to_rank.introduced_chapter
                and to_rank.introduced_chapter > chapter
            ):
                continue

            breakthrough = "NO_CHANGE"
            if from_rank and to_rank:
                breakthrough = RankComparisonService.detect_breakthrough(
                    from_rank.order, to_rank.order
                )
            elif to_rank and not from_rank:
                breakthrough = "BREAKTHROUGH"

            hydrated_transitions.append(
                {
                    "from_rank_id": t.from_rank_id,
                    "from_rank_name": from_rank.name if from_rank else None,
                    "to_rank_id": t.to_rank_id,
                    "to_rank_name": to_rank.name if to_rank else None,
                    "chapter": t.chapter,
                    "event_id": t.event_id,
                    "breakthrough_status": breakthrough,
                }
            )

        current_rank_meta = (
            entities.ranks.get(progression.current_rank)
            if progression.current_rank
            else None
        )
        if (
            current_rank_meta
            and current_rank_meta.introduced_chapter
            and current_rank_meta.introduced_chapter > chapter
        ):
            # Mask future rank
            current_rank_meta = None

        return {
            "character_id": character_id,
            "power_system_id": power_system_id,
            "current_rank": {
                "id": progression.current_rank,
                "name": current_rank_meta.name if current_rank_meta else None,
                "order": current_rank_meta.order if current_rank_meta else None,
            }
            if current_rank_meta
            else None,
            "transitions": hydrated_transitions,
        }
