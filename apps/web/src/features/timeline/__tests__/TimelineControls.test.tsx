import { render, screen, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ReaderProvider } from '../../reader/reader-store';
import { TimelineControls } from '../components/TimelineControls';
import { describe, it, expect } from 'vitest';

const renderControls = (chapter: number) => {
  return render(
    <MemoryRouter initialEntries={[`/series/test?chapter=${chapter}`]}>
      <ReaderProvider seriesId="test">
        <TimelineControls totalChapters={100} />
      </ReaderProvider>
    </MemoryRouter>
  );
};

describe('TimelineControls', () => {
  it('disables previous at chapter 1', () => {
    renderControls(1);
    const prevBtn = screen.getByText('[◀]') as HTMLButtonElement;
    expect(prevBtn.disabled).toBe(true);
  });

  it('disables next at max chapter', () => {
    renderControls(100);
    const nextBtn = screen.getByText('[▶]') as HTMLButtonElement;
    expect(nextBtn.disabled).toBe(true);
  });

  it('updates url on next click', () => {
    renderControls(50);
    const nextBtn = screen.getByText('[▶]') as HTMLButtonElement;
    act(() => nextBtn.click());
    expect(screen.getByText('Reader Chapter: 51')).toBeTruthy();
  });
});
