import { CharacterStateResponse, CharacterResponse } from '../../../types/api';

export interface MergedCharacter {
  id: string;
  name: string;
  state: CharacterStateResponse;
}

export const mergeCharactersWithWorldState = (
  characters: CharacterResponse[],
  worldStateCharacters: Record<string, CharacterStateResponse>,
  searchQuery: string = ''
): MergedCharacter[] => {
  const merged: MergedCharacter[] = [];
  
  for (const char of characters) {
    const wsState = worldStateCharacters[char.id];
    // Spoiler Firewall: If character has no state in the WorldState at this chapter,
    // they haven't been introduced yet. Drop them aggressively.
    if (wsState && wsState.exists) {
      merged.push({
        id: char.id,
        name: char.name,
        state: wsState
      });
    }
  }

  if (!searchQuery.trim()) {
    return merged;
  }
  
  const query = searchQuery.toLowerCase();
  return merged.filter(c => c.name.toLowerCase().includes(query));
};
