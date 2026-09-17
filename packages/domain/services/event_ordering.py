from dataclasses import dataclass

from ..entities.event import Event
from ..value_objects.chapter_number import ChapterNumber


@dataclass(frozen=True)
class EventEnvelope:
    event: Event
    chapter_number: ChapterNumber


def sort_events(envelopes: list[EventEnvelope]) -> list[EventEnvelope]:
    """
    Deterministically sorts events based on:
    1. Chapter Number
    2. Sequence
    3. Event ID (as string)
    """
    return sorted(
        envelopes,
        key=lambda env: (
            env.chapter_number.value,
            env.event.sequence,
            str(env.event.id.value),
        ),
    )
