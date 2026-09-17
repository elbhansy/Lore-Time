import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReaderProvider } from '../../reader/reader-store';
import { CharacterProfile } from '../components/CharacterProfile';
import { describe, it, expect, vi } from 'vitest';
import * as hooksMod from '../hooks/useCharacters';

vi.mock('../hooks/useCharacters', () => ({
  useCharacterProfile: vi.fn(),
  useCharacters: vi.fn()
}));
vi.mock('../../world-state/queries', () => ({
  useTimeline: vi.fn().mockReturnValue({ data: [], isLoading: false })
}));

const renderProfile = (chapter: number, characterId: string) => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/series/test/characters/${characterId}?chapter=${chapter}`]}>
        <Routes>
          <Route path="/series/:seriesId/characters/:characterId" element={
            <ReaderProvider seriesId="test">
              <CharacterProfile />
            </ReaderProvider>
          } />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('CharacterProfile', () => {
  it('blocks rendering of unintroduced characters (Spoiler Firewall)', () => {
    // Mock the hook to return a character with exists=false (not introduced yet)
    vi.mocked(hooksMod.useCharacterProfile).mockReturnValue({
      data: {
        id: '1', name: 'Future Char', as_of_chapter: 100,
        state: { exists: false, alive: true, rank: null, unlocked_skills: [], faction_id: null }
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn()
    } as any);

    renderProfile(50, '1');
    
    expect(screen.getByText(/This character has not been introduced as of Chapter 50/i)).toBeTruthy();
  });

  it('renders introduced character profile safely', () => {
    vi.mocked(hooksMod.useCharacterProfile).mockReturnValue({
      data: {
        id: '1', name: 'Safe Char', as_of_chapter: 100,
        state: { exists: true, alive: true, rank: 'S', unlocked_skills: ['Fireball'], faction_id: 'Guild' }
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn()
    } as any);

    renderProfile(100, '1');
    
    expect(screen.getByText('Safe Char')).toBeTruthy();
    expect(screen.getByText('As of Chapter 100')).toBeTruthy();
    expect(screen.getByText('ALIVE')).toBeTruthy();
    expect(screen.getByText('S')).toBeTruthy();
  });
});
