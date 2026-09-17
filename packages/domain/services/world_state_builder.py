from packages.domain.services.event_applier import EventApplier
from packages.domain.services.event_ordering import EventEnvelope, sort_events
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId


class WorldStateBuilder:
    def __init__(self, event_applier: EventApplier):
        self.event_applier = event_applier

    def build(
        self,
        series_id: EntityId,
        envelopes: list[EventEnvelope],
        reader_chapter: ChapterNumber,
    ) -> WorldState:
        """
        Builds the WorldState for a specific series at a specific reader chapter.
        Enforces the Spoiler Firewall by ignoring future events.
        """
        # 1. Initialize empty state
        state = WorldState(series_id=series_id, chapter=reader_chapter)

        # 2. Spoiler Firewall: Filter out future events
        visible_envelopes = [
            env for env in envelopes if env.chapter_number <= reader_chapter
        ]

        # 3. Deterministic Sort
        sorted_envelopes = sort_events(visible_envelopes)

        # 4. Apply Events sequentially
        for env in sorted_envelopes:
            self.event_applier.apply(state, env)

        return state
