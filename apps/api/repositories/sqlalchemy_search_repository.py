from sqlalchemy import String, or_
from sqlalchemy.orm import Session

from infrastructure.database.models.character import CharacterModel
from infrastructure.database.models.event import EventModel
from infrastructure.database.models.faction import FactionModel
from infrastructure.database.models.power_system import PowerSystemModel
from infrastructure.database.models.rank import RankModel
from infrastructure.database.models.skill import SkillModel
from packages.domain.repositories.search_repository import SearchRepository
from packages.domain.search.search_query import SearchQuery
from packages.domain.search.search_result import SearchResult
from packages.domain.search.search_type import SearchType


class SQLAlchemySearchRepository(SearchRepository):
    def __init__(self, session: Session):
        self.session = session

    def search_candidates(
        self, query: SearchQuery, series_id: str
    ) -> list[SearchResult]:
        candidates = []
        text = f"%{query.text}%"

        # We fetch without pagination here, because pagination must be applied AFTER visibility filtering
        # in the Domain/Use Case layer. To prevent massive memory loads, we could limit to a reasonable upper bound
        # like 1000 candidates per query type.
        MAX_CANDIDATES = 1000

        # Character
        if query.type in [SearchType.ALL, SearchType.CHARACTER]:
            chars = (
                self.session.query(CharacterModel)
                .filter(
                    CharacterModel.series_id == series_id,
                    or_(
                        CharacterModel.name.ilike(text),
                        CharacterModel.description.ilike(text),
                    ),
                )
                .limit(MAX_CANDIDATES)
                .all()
            )
            for c in chars:
                candidates.append(
                    SearchResult(
                        id=c.id,
                        type=SearchType.CHARACTER,
                        title=c.name,
                        description=c.description,
                    )
                )

        # Faction
        if query.type in [SearchType.ALL, SearchType.FACTION]:
            factions = (
                self.session.query(FactionModel)
                .filter(
                    FactionModel.series_id == series_id, FactionModel.name.ilike(text)
                )
                .limit(MAX_CANDIDATES)
                .all()
            )
            for f in factions:
                candidates.append(
                    SearchResult(
                        id=f.id, type=SearchType.FACTION, title=f.name, description=None
                    )
                )

        # Skill
        if query.type in [SearchType.ALL, SearchType.SKILL]:
            skills = (
                self.session.query(SkillModel)
                .join(
                    PowerSystemModel, SkillModel.power_system_id == PowerSystemModel.id
                )
                .filter(
                    PowerSystemModel.series_id == series_id, SkillModel.name.ilike(text)
                )
                .limit(MAX_CANDIDATES)
                .all()
            )
            for s in skills:
                candidates.append(
                    SearchResult(
                        id=s.id, type=SearchType.SKILL, title=s.name, description=None
                    )
                )

        # Power System
        if query.type in [SearchType.ALL, SearchType.POWER_SYSTEM]:
            systems = (
                self.session.query(PowerSystemModel)
                .filter(
                    PowerSystemModel.series_id == series_id,
                    or_(
                        PowerSystemModel.name.ilike(text),
                        PowerSystemModel.description.ilike(text),
                    ),
                )
                .limit(MAX_CANDIDATES)
                .all()
            )
            for sys in systems:
                candidates.append(
                    SearchResult(
                        id=sys.id,
                        type=SearchType.POWER_SYSTEM,
                        title=sys.name,
                        description=sys.description,
                    )
                )

        # Rank
        if query.type in [SearchType.ALL, SearchType.RANK]:
            ranks = (
                self.session.query(RankModel)
                .join(
                    PowerSystemModel, RankModel.power_system_id == PowerSystemModel.id
                )
                .filter(
                    PowerSystemModel.series_id == series_id,
                    or_(RankModel.name.ilike(text), RankModel.description.ilike(text)),
                )
                .limit(MAX_CANDIDATES)
                .all()
            )
            for r in ranks:
                # Store system_id in metadata for later lookup if needed, but DO NOT leak future rank metadata.
                candidates.append(
                    SearchResult(
                        id=r.id,
                        type=SearchType.RANK,
                        title=r.name,
                        description=r.description,
                    )
                )

        # Event
        if query.type in [SearchType.ALL, SearchType.EVENT]:
            # For events, we search the JSON or string representations if available.
            from sqlalchemy.orm import joinedload

            events = (
                self.session.query(EventModel)
                .options(joinedload(EventModel.chapter))
                .filter(
                    EventModel.series_id == series_id,
                    EventModel.new_state.cast(String).ilike(text),
                )
                .limit(MAX_CANDIDATES)
                .all()
            )

            for e in events:
                desc = f"Event {e.type} involving {e.subject_id}"
                ch_num = e.chapter.number if e.chapter else 1
                candidates.append(
                    SearchResult(
                        id=e.id,
                        type=SearchType.EVENT,
                        title=e.type,
                        description=desc,
                        metadata={"chapter": ch_num},
                    )
                )

        return candidates
