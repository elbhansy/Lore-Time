import { describe, it, expect } from 'vitest';
import { mergeCharactersWithWorldState } from '../utils/character-utils';
import { CharacterResponse, CharacterStateResponse } from '../../../types/api';

const makeChar = (id: string, name: string): CharacterResponse => ({
  id, name, state: { exists: false, alive: false, rank: null, unlocked_skills: [], faction_id: null }, as_of_chapter: 0
});

const makeState = (exists: boolean, alive: boolean, rank: string | null = null): CharacterStateResponse => ({
  exists, alive, rank, unlocked_skills: [], faction_id: null
});

describe('character-utils', () => {
  it('merges characters and correctly drops unintroduced ones (Spoiler Firewall)', () => {
    const chars = [
      makeChar('1', 'Jin'),
      makeChar('2', 'Alex'),
      makeChar('3', 'Future Villain')
    ];
    
    // Future Villain has exists=false or is undefined in WorldState
    const worldState = {
      '1': makeState(true, true, 'B'),
      '2': makeState(true, false, 'C'),
      '3': makeState(false, true)
    };
    
    const merged = mergeCharactersWithWorldState(chars, worldState, '');
    
    expect(merged).toHaveLength(2);
    expect(merged.find(c => c.id === '1')).toBeDefined();
    expect(merged.find(c => c.id === '2')).toBeDefined();
    
    // MUST NOT CONTAIN Future Villain
    expect(merged.find(c => c.id === '3')).toBeUndefined();
  });

  it('filters by search query', () => {
    const chars = [
      makeChar('1', 'Jin Woo'),
      makeChar('2', 'Alex'),
    ];
    
    const worldState = {
      '1': makeState(true, true),
      '2': makeState(true, true)
    };
    
    const merged = mergeCharactersWithWorldState(chars, worldState, 'jin');
    
    expect(merged).toHaveLength(1);
    expect(merged[0].name).toBe('Jin Woo');
  });
});
