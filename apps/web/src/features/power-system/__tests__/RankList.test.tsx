import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RankList } from '../components/RankList';
import { RankResponse } from '../../../types/api';

const makeRank = (id: string, name: string, order: number, introduced_chapter: number): RankResponse => ({
  id, power_system_id: 'ps1', name, slug: name.toLowerCase(), order, introduced_chapter, description: null, parent_rank_id: null
});

describe('RankList', () => {
  it('renders ranks sorted by order, not name', () => {
    // S comes after B and A alphabetically, but let's test order field
    // order 1 = B, order 2 = S, order 3 = A
    const ranks = [
      makeRank('3', 'A Rank', 3, 10),
      makeRank('1', 'B Rank', 1, 1),
      makeRank('2', 'S Rank', 2, 5),
    ];

    render(<RankList ranks={ranks} />);
    
    const elements = screen.getAllByText(/Rank/);
    expect(elements).toHaveLength(3);
    
    // Should be B, S, A
    expect(elements[0].textContent).toContain('B Rank');
    expect(elements[1].textContent).toContain('S Rank');
    expect(elements[2].textContent).toContain('A Rank');
  });

  it('displays the introduced chapter correctly', () => {
    const ranks = [makeRank('1', 'Mortal', 1, 150)];
    render(<RankList ranks={ranks} />);
    
    expect(screen.getByText('(Introduced Ch. 150)')).toBeTruthy();
  });
});
