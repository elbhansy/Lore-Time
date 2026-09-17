from fastapi import Depends

from apps.api.app.application.characters.get_character import GetCharacterUseCase
from apps.api.app.application.characters.get_characters import GetCharactersUseCase
from apps.api.app.application.power_system.get_power_systems import (
    GetPowerSystemsUseCase,
)
from apps.api.app.application.power_system.get_rank_progression import (
    GetRankProgressionUseCase,
)
from apps.api.app.application.power_system.get_ranks import GetRanksUseCase
from apps.api.app.application.relationships.get_character_graph import (
    GetCharacterGraphUseCase,
)
from apps.api.app.application.relationships.get_relationship_graph import (
    GetRelationshipGraphUseCase,
)
from apps.api.app.application.relationships.get_relationship_history import (
    GetRelationshipHistoryUseCase,
)
from apps.api.app.application.timeline.get_timeline_events import (
    GetTimelineEventsUseCase,
)
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.world_state_builder import WorldStateBuilder

from .repositories import (
    get_character_repository,
    get_event_repository,
    get_power_system_repository,
    get_rank_repository,
    get_series_repository,
)


def get_event_applier() -> EventApplier:
    return EventApplier()


def get_world_state_builder(
    applier: EventApplier = Depends(get_event_applier),
) -> WorldStateBuilder:
    return WorldStateBuilder(applier)


def get_world_state_use_case(
    series_repo=Depends(get_series_repository),
    event_repo=Depends(get_event_repository),
    builder=Depends(get_world_state_builder),
) -> GetWorldStateUseCase:
    return GetWorldStateUseCase(series_repo, event_repo, builder)


def get_timeline_events_use_case(
    series_repo=Depends(get_series_repository), event_repo=Depends(get_event_repository)
) -> GetTimelineEventsUseCase:
    return GetTimelineEventsUseCase(series_repo, event_repo)


def get_character_use_case(
    character_repo=Depends(get_character_repository),
    get_world_state_uc=Depends(get_world_state_use_case),
) -> GetCharacterUseCase:
    return GetCharacterUseCase(character_repo, get_world_state_uc)


def get_characters_use_case(
    character_repo=Depends(get_character_repository),
    series_repo=Depends(get_series_repository),
) -> GetCharactersUseCase:
    return GetCharactersUseCase(character_repo, series_repo)


def get_power_systems_use_case(
    ps_repo=Depends(get_power_system_repository),
    series_repo=Depends(get_series_repository),
) -> GetPowerSystemsUseCase:
    return GetPowerSystemsUseCase(ps_repo, series_repo)


def get_ranks_use_case(
    rank_repo=Depends(get_rank_repository), ps_repo=Depends(get_power_system_repository)
) -> GetRanksUseCase:
    return GetRanksUseCase(rank_repo, ps_repo)


def get_rank_progression_use_case(
    event_repo=Depends(get_event_repository), rank_repo=Depends(get_rank_repository)
) -> GetRankProgressionUseCase:
    return GetRankProgressionUseCase(event_repo, rank_repo)


def get_relationship_graph_use_case(
    character_repo=Depends(get_character_repository),
    world_state_uc=Depends(get_world_state_use_case),
) -> GetRelationshipGraphUseCase:
    return GetRelationshipGraphUseCase(character_repo, world_state_uc)


def get_character_graph_use_case(
    character_repo=Depends(get_character_repository),
    world_state_uc=Depends(get_world_state_use_case),
) -> GetCharacterGraphUseCase:
    return GetCharacterGraphUseCase(character_repo, world_state_uc)


def get_relationship_history_use_case(
    event_repo=Depends(get_event_repository),
    character_repo=Depends(get_character_repository),
) -> GetRelationshipHistoryUseCase:
    return GetRelationshipHistoryUseCase(event_repo, character_repo)


def get_narrative_intelligence_engine():
    from packages.domain.services.narrative_intelligence_engine import (
        NarrativeIntelligenceEngine,
    )

    return NarrativeIntelligenceEngine()


def get_character_arc_use_case(
    series_repo=Depends(get_series_repository),
    character_repo=Depends(get_character_repository),
    event_repo=Depends(get_event_repository),
    builder=Depends(get_world_state_builder),
    narrative_engine=Depends(get_narrative_intelligence_engine),
):
    from apps.api.app.application.narrative.get_character_arc import (
        GetCharacterArcUseCase,
    )

    return GetCharacterArcUseCase(
        series_repo=series_repo,
        character_repo=character_repo,
        event_repo=event_repo,
        world_state_builder=builder,
        narrative_engine=narrative_engine,
    )


def get_causal_intelligence_service():
    from packages.domain.services.causal_intelligence_service import (
        CausalIntelligenceService,
    )

    return CausalIntelligenceService()


def get_character_causality_use_case(
    series_repo=Depends(get_series_repository),
    character_repo=Depends(get_character_repository),
    event_repo=Depends(get_event_repository),
    builder=Depends(get_world_state_builder),
    causal_service=Depends(get_causal_intelligence_service),
):
    from apps.api.app.application.causality.get_character_causality import (
        GetCharacterCausalityUseCase,
    )

    return GetCharacterCausalityUseCase(
        series_repo=series_repo,
        character_repo=character_repo,
        event_repo=event_repo,
        world_state_builder=builder,
        causal_service=causal_service,
    )


def get_temporal_narrative_synthesis_service(
    causal_service=Depends(get_causal_intelligence_service),
    narrative_engine=Depends(get_narrative_intelligence_engine),
):
    from packages.domain.services.temporal_narrative_synthesis_service import (
        TemporalNarrativeSynthesisService,
    )

    return TemporalNarrativeSynthesisService(
        causal_service=causal_service,
        narrative_engine=narrative_engine,
    )


def get_event_narrative_use_case(
    series_repo=Depends(get_series_repository),
    event_repo=Depends(get_event_repository),
    builder=Depends(get_world_state_builder),
    synthesis_service=Depends(get_temporal_narrative_synthesis_service),
):
    from apps.api.app.application.synthesis.get_narrative_synthesis import (
        GetEventNarrativeExplanationUseCase,
    )

    return GetEventNarrativeExplanationUseCase(
        series_repo=series_repo,
        event_repo=event_repo,
        world_state_builder=builder,
        synthesis_service=synthesis_service,
    )


def get_character_narrative_causality_use_case(
    series_repo=Depends(get_series_repository),
    character_repo=Depends(get_character_repository),
    event_repo=Depends(get_event_repository),
    builder=Depends(get_world_state_builder),
    synthesis_service=Depends(get_temporal_narrative_synthesis_service),
):
    from apps.api.app.application.synthesis.get_narrative_synthesis import (
        GetCharacterNarrativeCausalityUseCase,
    )

    return GetCharacterNarrativeCausalityUseCase(
        series_repo=series_repo,
        character_repo=character_repo,
        event_repo=event_repo,
        world_state_builder=builder,
        synthesis_service=synthesis_service,
    )


def get_intelligence_query_service(
    series_repo=Depends(get_series_repository),
    character_repo=Depends(get_character_repository),
    event_repo=Depends(get_event_repository),
    builder=Depends(get_world_state_builder),
    narrative_engine=Depends(get_narrative_intelligence_engine),
    causal_service=Depends(get_causal_intelligence_service),
):
    from apps.api.app.application.intelligence.intelligence_query_service import (
        IntelligenceQueryService,
    )

    return IntelligenceQueryService(
        series_repo=series_repo,
        character_repo=character_repo,
        event_repo=event_repo,
        world_state_builder=builder,
        narrative_engine=narrative_engine,
        causal_service=causal_service,
    )
