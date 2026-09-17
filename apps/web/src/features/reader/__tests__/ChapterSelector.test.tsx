import { render, screen, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ReaderProvider } from '../reader-store';
import { ChapterSelector } from '../components/ChapterSelector';
import { describe, it, expect } from 'vitest';

const renderWithContext = (initialChapter = 10, totalChapters = 100) => {
  return render(
    <MemoryRouter initialEntries={[`/series/test?chapter=${initialChapter}`]}>
      <ReaderProvider seriesId="test">
        <ChapterSelector totalChapters={totalChapters} />
      </ReaderProvider>
    </MemoryRouter>
  );
};

describe('ChapterSelector', () => {
  it('renders correctly with context chapter', () => {
    renderWithContext(10, 100);
    expect(screen.getByText('Chapter 10 / 100')).toBeTruthy();
  });

  it('increments chapter', () => {
    renderWithContext(10, 100);
    const incButton = screen.getByText('[+]');
    act(() => {
      incButton.click();
    });
    expect(screen.getByText('Chapter 11 / 100')).toBeTruthy();
  });

  it('decrements chapter', () => {
    renderWithContext(10, 100);
    const decButton = screen.getByText('[-]');
    act(() => {
      decButton.click();
    });
    expect(screen.getByText('Chapter 9 / 100')).toBeTruthy();
  });

  it('disables decrement at chapter 1', () => {
    renderWithContext(1, 100);
    const decButton = screen.getByText('[-]') as HTMLButtonElement;
    expect(decButton.disabled).toBe(true);
  });

  it('disables increment at total chapters', () => {
    renderWithContext(100, 100);
    const incButton = screen.getByText('[+]') as HTMLButtonElement;
    expect(incButton.disabled).toBe(true);
  });
});
