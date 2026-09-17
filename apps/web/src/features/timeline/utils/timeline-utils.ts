import { EventResponse } from '../../../types/api';
import { TimelineChapter, TimelineCategory } from '../types';

export const getEventCategory = (type: string): TimelineCategory => {
  switch (type) {
    case 'CHARACTER_INTRODUCED':
    case 'CHARACTER_DIED':
      return 'Characters';
    case 'POWER_RANK_CHANGED':
    case 'SKILL_UNLOCKED':
    case 'SKILL_UPGRADED':
      return 'Power';
    case 'FACTION_JOINED':
    case 'FACTION_LEFT':
      return 'Factions';
    case 'RELATIONSHIP_CREATED':
    case 'RELATIONSHIP_CHANGED':
    case 'RELATIONSHIP_ENDED':
      return 'Relationships';
    default:
      return 'All';
  }
};

export const filterEventsByCategory = (events: EventResponse[], category: TimelineCategory): EventResponse[] => {
  if (category === 'All') return events;
  return events.filter(e => getEventCategory(e.type) === category);
};

export const groupEventsByChapter = (events: EventResponse[], readerChapter: number): TimelineChapter[] => {
  // Defensive Spoiler Firewall: Drop any event that is somehow in the future
  const safeEvents = events.filter(e => e.chapter_number <= readerChapter);

  const groups = safeEvents.reduce((acc, event) => {
    if (!acc[event.chapter_number]) {
      acc[event.chapter_number] = [];
    }
    acc[event.chapter_number].push(event);
    return acc;
  }, {} as Record<number, EventResponse[]>);

  // Convert to sorted array
  const sortedChapters = Object.keys(groups)
    .map(k => parseInt(k, 10))
    .sort((a, b) => a - b);

  return sortedChapters.map(chapterNum => {
    // Sort events within chapter deterministically
    const chapterEvents = groups[chapterNum].sort((a, b) => {
      if (a.sequence !== b.sequence) return a.sequence - b.sequence;
      return a.id.localeCompare(b.id);
    });

    return {
      number: chapterNum,
      events: chapterEvents,
      isCurrent: chapterNum === readerChapter
    };
  });
};
