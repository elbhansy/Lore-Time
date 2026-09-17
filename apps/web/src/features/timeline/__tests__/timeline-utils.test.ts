import { describe, it, expect } from 'vitest';
import { groupEventsByChapter, getEventCategory, filterEventsByCategory } from '../utils/timeline-utils';
import { EventResponse } from '../../../types/api';

const makeEvent = (id: string, chapter: number, sequence: number, type: string): EventResponse => ({
  id, chapter_number: chapter, sequence, type, subject_type: 'CHAR', subject_id: '1', target_type: null, target_id: null, metadata: {}
});

describe('timeline-utils', () => {
  it('groups events by chapter and sorts by sequence and id', () => {
    const events = [
      makeEvent('c', 10, 2, 'T'),
      makeEvent('a', 10, 1, 'T'),
      makeEvent('b', 10, 2, 'T'),
      makeEvent('d', 5, 1, 'T'),
    ];
    
    const chapters = groupEventsByChapter(events, 100);
    
    expect(chapters).toHaveLength(2);
    expect(chapters[0].number).toBe(5);
    expect(chapters[1].number).toBe(10);
    
    const ch10Events = chapters[1].events;
    expect(ch10Events[0].id).toBe('a');
    expect(ch10Events[1].id).toBe('b'); // sequence 2, id 'b' comes before 'c'
    expect(ch10Events[2].id).toBe('c');
  });

  it('defensively drops events beyond readerChapter (Spoiler Firewall)', () => {
    const events = [
      makeEvent('1', 50, 1, 'POWER_RANK_CHANGED'),
      makeEvent('2', 100, 1, 'POWER_RANK_CHANGED'),
      makeEvent('3', 200, 1, 'POWER_RANK_CHANGED'),
    ];
    
    const chapters = groupEventsByChapter(events, 100);
    
    expect(chapters).toHaveLength(2);
    expect(chapters[0].number).toBe(50);
    expect(chapters[1].number).toBe(100);
    // Chapter 200 MUST NOT exist
    expect(chapters.find(c => c.number === 200)).toBeUndefined();
  });
});
