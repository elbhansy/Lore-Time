import uuid

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from apps.api.app.core.cache import CacheService, get_cache_service
from packages.domain.repositories.search_repository import SearchRepository
from packages.domain.search.search_page import SearchPage
from packages.domain.search.search_query import SearchQuery, SearchType
from packages.domain.search.search_result import SearchResult
from packages.domain.value_objects.entity_id import EntityId


class GlobalSearchUseCase:
    def __init__(
        self,
        search_repo: SearchRepository,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
        cache_service: CacheService | None = None,
    ):
        self.search_repo = search_repo
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider
        self.cache_service = cache_service or get_cache_service()

    def execute(self, series_id: uuid.UUID, query: SearchQuery) -> SearchPage:
        def compute_search() -> SearchPage:
            # 1. Fetch DB candidates
            candidates = self.search_repo.search_candidates(query, str(series_id))

            # 2. Reconstruct Temporal State
            ws = self.get_world_state_uc.execute(series_id, query.reader_chapter)
            static_entities = self.entities_provider.get_static_entities(
                EntityId(series_id)
            )

            # 3. Apply Visibility Firewall
            visible_results = []
            for c in candidates:
                if self._is_visible(c, ws, static_entities, query.reader_chapter):
                    # Clean up any potentially leaked future metadata in the description or metadata
                    self._sanitize_result(c)
                    visible_results.append(c)

            # 4. Deterministic Ranking
            # Sort by: type -> title -> id
            visible_results.sort(key=lambda x: (x.type.value, x.title or "", x.id))

            # 5. Pagination & Count
            total = len(visible_results)
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size

            page_items = visible_results[start_idx:end_idx]
            has_next = end_idx < total

            return SearchPage(
                items=page_items,
                page=query.page,
                page_size=query.page_size,
                total=total,
                has_next=has_next,
            )

        query_params = {
            "text": query.text,
            "type": query.type.value
            if hasattr(query.type, "value")
            else str(query.type),
            "page": query.page,
            "page_size": query.page_size,
        }

        return self.cache_service.get_or_compute(
            series_id=series_id,
            resource="search",
            compute_fn=compute_search,
            reader_chapter=query.reader_chapter,
            query_params=query_params,
        )

    def _is_visible(
        self, result: SearchResult, ws, static_entities, reader_chapter: int
    ) -> bool:
        if result.type == SearchType.CHARACTER:
            char_state = ws.characters.get(EntityId(result.id)) or ws.characters.get(
                str(result.id)
            )
            return char_state is not None and char_state.exists

        elif result.type == SearchType.FACTION:
            fac_meta = static_entities.factions.get(result.id)
            return (
                fac_meta is not None
                and fac_meta.introduced_chapter
                and fac_meta.introduced_chapter <= reader_chapter
            )

        elif result.type == SearchType.SKILL:
            # Skill is visible if someone unlocked it before/at reader_chapter
            # OR if it was statically introduced. We check static first.
            skill_meta = static_entities.skills.get(result.id)
            if (
                skill_meta
                and skill_meta.introduced_chapter
                and skill_meta.introduced_chapter <= reader_chapter
            ):
                return True
            # Check if anyone unlocked it
            for skills_list in ws.skills.values():
                for s in skills_list:
                    if s.skill_id == result.id and s.unlocked_at <= reader_chapter:
                        return True
            return False

        elif result.type == SearchType.POWER_SYSTEM:
            ps_meta = static_entities.power_systems.get(result.id)
            return ps_meta is not None and (
                not ps_meta.introduced_chapter
                or ps_meta.introduced_chapter <= reader_chapter
            )

        elif result.type == SearchType.RANK:
            rank_meta = static_entities.ranks.get(result.id)
            return (
                rank_meta is not None
                and rank_meta.introduced_chapter
                and rank_meta.introduced_chapter <= reader_chapter
            )

        elif result.type == SearchType.EVENT:
            event_chap = result.metadata.get("chapter", float("inf"))
            return event_chap <= reader_chapter

        return False

    def _sanitize_result(self, result: SearchResult):
        # Ensure we don't leak metadata if it wasn't explicitly allowed
        if result.type == SearchType.EVENT:
            result.metadata.pop("chapter", None)
