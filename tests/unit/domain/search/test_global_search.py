import uuid

from apps.api.app.application.search.global_search import GlobalSearchUseCase
from packages.domain.search.search_query import SearchQuery, SearchType
from packages.domain.search.search_result import SearchResult
from packages.domain.state.character_state import CharacterState
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId


class MockSearchRepo:
    def search_candidates(self, query, series_id):
        return [
            SearchResult(id="c1", type=SearchType.CHARACTER, title="Visible Char"),
            SearchResult(id="c2", type=SearchType.CHARACTER, title="Future Char"),
            SearchResult(id="f1", type=SearchType.FACTION, title="Visible Faction"),
            SearchResult(id="f2", type=SearchType.FACTION, title="Future Faction"),
            SearchResult(
                id="e1",
                type=SearchType.EVENT,
                title="Visible Event",
                metadata={"chapter": 50},
            ),
            SearchResult(
                id="e2",
                type=SearchType.EVENT,
                title="Future Event",
                metadata={"chapter": 200},
            ),
        ]


class MockGetWorldStateUseCase:
    def execute(self, series_id, chapter):
        ws = WorldState(series_id=EntityId(series_id), chapter=ChapterNumber(chapter))
        # c1 exists, c2 doesn't exist yet at chapter 100
        ws.characters["c1"] = CharacterState(character_id=EntityId("c1"), exists=True)
        ws.characters["c2"] = CharacterState(character_id=EntityId("c2"), exists=False)
        return ws


class MockGraphEntitiesProvider:
    def get_static_entities(self, series_id):
        class Entities:
            def __init__(self):
                self.factions = {
                    "f1": type("Meta", (), {"introduced_chapter": 10})(),
                    "f2": type("Meta", (), {"introduced_chapter": 150})(),
                }
                self.skills = {}
                self.power_systems = {}
                self.ranks = {}

        return Entities()


def test_visibility_and_anti_leak():
    repo = MockSearchRepo()
    ws_uc = MockGetWorldStateUseCase()
    provider = MockGraphEntitiesProvider()

    uc = GlobalSearchUseCase(repo, ws_uc, provider)

    query = SearchQuery(
        text="test", type=SearchType.ALL, reader_chapter=100, page=1, page_size=10
    )

    page = uc.execute(uuid.uuid4(), query)

    # At chapter 100, we expect:
    # c1 (exists=True), c2 (exists=False) -> c1 only
    # f1 (intro=10), f2 (intro=150) -> f1 only
    # e1 (ch=50), e2 (ch=200) -> e1 only

    assert page.total == 3
    assert len(page.items) == 3

    ids = [item.id for item in page.items]
    assert "c1" in ids
    assert "f1" in ids
    assert "e1" in ids
    assert "c2" not in ids
    assert "f2" not in ids
    assert "e2" not in ids

    # Check deterministic ordering (type -> title -> id)
    # CHARACTER (c1) -> EVENT (e1) -> FACTION (f1)
    # Note: enum value ordering might vary slightly but should be consistent
    assert page.items[0].id == "c1"  # CHARACTER
    assert page.items[1].id == "e1"  # EVENT
    assert page.items[2].id == "f1"  # FACTION
