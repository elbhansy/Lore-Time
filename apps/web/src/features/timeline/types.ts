import { EventResponse } from '../../types/api';

export type TimelineCategory = 'All' | 'Characters' | 'Power' | 'Factions' | 'Relationships';

export interface TimelineChapter {
  number: number;
  events: EventResponse[];
  isCurrent: boolean;
}
