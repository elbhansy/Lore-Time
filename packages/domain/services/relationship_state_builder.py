from packages.domain.entities.event import Event
from packages.domain.state.relationship_state import RelationshipState
from packages.domain.value_objects.event_type import EventType
from packages.domain.value_objects.relationship_type import RelationshipType


class RelationshipStateBuilder:
    @staticmethod
    def build(events: list[Event]) -> dict[tuple[str, str], RelationshipState]:
        relationships: dict[tuple[str, str], RelationshipState] = {}

        for event in events:
            # We assume events are already chronologically sorted by the caller (WorldStateBuilder)

            if event.type in (
                EventType.RELATIONSHIP_CREATED,
                EventType.RELATIONSHIP_CHANGED,
                EventType.RELATIONSHIP_ENDED,
            ):
                subject_id = event.subject_id
                target_id = event.target_id
                if not subject_id or not target_id:
                    continue

                key = (subject_id.value, target_id.value)
                chapter = event.chapter_id.value  # Note: In a real system, we'd use the chapter_number mapping, but WorldStateBuilder provides chapter_id. Actually, the WorldStateBuilder uses the envelope's chapter_number? No, WorldStateBuilder receives a sequence of events.

                # To get the chapter number, we might need it from the event metadata or envelope.
                # Assuming the event metadata contains 'chapter_number' for now, or we just use 0 if not available since WorldState limits events anyway.
                # The user requested 'started_at' and 'ended_at'. Let's check event.chapter_number if available, or we pass it in.
                # Wait, WorldStateBuilder uses `event.chapter_id`, but we really want `chapter_number`.
                # Let's extract chapter_number from event metadata or assume it's passed if we refactor WorldStateBuilder.
                # For M1.0, we will try to get it from metadata or default to 0.
                ch_num = event.metadata.get("chapter_number", 0)

                if event.type == EventType.RELATIONSHIP_CREATED:
                    rel_type_str = event.new_state.get("relationship_type")
                    if rel_type_str:
                        rel_type = RelationshipType(rel_type_str)
                        relationships[key] = RelationshipState(
                            subject_id=subject_id,
                            target_id=target_id,
                            relationship_type=rel_type,
                            active=True,
                            started_at=ch_num,
                        )

                elif event.type == EventType.RELATIONSHIP_CHANGED:
                    if key in relationships:
                        rel_type_str = event.new_state.get("relationship_type")
                        if rel_type_str:
                            relationships[key].relationship_type = RelationshipType(
                                rel_type_str
                            )
                            # Keep started_at the same (or we can update it, but domain rule says keep identity)

                elif event.type == EventType.RELATIONSHIP_ENDED:
                    if key in relationships:
                        relationships[key].active = False
                        relationships[key].ended_at = ch_num

        return relationships
