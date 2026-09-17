import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RankProgression } from '../components/RankProgression';
import { RankResponse } from '../../../types/api';

const makeRank = (id: string, name: string): RankResponse => ({
  id, power_system_id: 'ps1', name, slug: name.toLowerCase(), order: 1, introduced_chapter: 1, description: null, parent_rank_id: null
});

describe('RankProgression', () => {
  it('renders a progression chain correctly', () => {
    const ranks = [
      makeRank('1', 'B Rank'),
      makeRank('2', 'A Rank'),
      makeRank('3', 'S Rank'),
    ];

    render(<RankProgression ranks={ranks} />);
    
    expect(screen.getByText('B Rank')).toBeTruthy();
    expect(screen.getByText('A Rank')).toBeTruthy();
    expect(screen.getByText('S Rank')).toBeTruthy();
    
    // Should have 2 arrows
    const arrows = screen.getAllByText('→');
    expect(arrows).toHaveLength(2);
  });
  
  it('renders fallback for empty progression', () => {
    render(<RankProgression ranks={[]} />);
    expect(screen.getByText('No rank changes recorded.')).toBeTruthy();
  });
});
