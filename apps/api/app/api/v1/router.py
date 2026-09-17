from fastapi import APIRouter

from .analytics import router as analytics_router
from .causality import router as causality_router
from .characters import router as characters_router
from .comparison import router as comparison_router
from .events import router as events_router
from .factions import router as factions_router
from .graph import router as graph_router
from .impact import router as impact_router
from .narrative import router as narrative_router
from .power import router as power_router
from .power_system import router as power_systems_router
from .read_models import router as read_models_router
from .relationships import router as relationships_router
from .search import router as search_router
from .skills import router as skills_router
from .synthesis import router as synthesis_router
from .timeline import router as timeline_router

api_router = APIRouter()

api_router.include_router(timeline_router)
api_router.include_router(characters_router)
api_router.include_router(power_systems_router)
api_router.include_router(relationships_router)
api_router.include_router(comparison_router)
api_router.include_router(impact_router)
api_router.include_router(graph_router)
api_router.include_router(factions_router)
api_router.include_router(skills_router)
api_router.include_router(power_router)
api_router.include_router(search_router)
api_router.include_router(events_router)
api_router.include_router(analytics_router)
api_router.include_router(narrative_router)
api_router.include_router(causality_router)
api_router.include_router(synthesis_router)
api_router.include_router(read_models_router)
