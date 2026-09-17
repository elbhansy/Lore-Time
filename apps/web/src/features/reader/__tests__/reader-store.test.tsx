import { render, screen, act } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { ReaderProvider, useReader } from '../reader-store';
import { describe, it, expect } from 'vitest';

const TestComponent = () => {
  const { readerChapter, setReaderChapter } = useReader();
  const location = useLocation();
  
  return (
    <div>
      <span data-testid="chapter">{readerChapter}</span>
      <span data-testid="url">{location.search}</span>
      <button onClick={() => setReaderChapter(50)}>Set to 50</button>
      <button onClick={() => setReaderChapter(-5)}>Set Invalid</button>
    </div>
  );
};

describe('ReaderProvider', () => {
  it('defaults to chapter 1 when URL is empty', () => {
    render(
      <MemoryRouter initialEntries={['/series/test']}>
        <ReaderProvider seriesId="test">
          <TestComponent />
        </ReaderProvider>
      </MemoryRouter>
    );
    expect(screen.getByTestId('chapter').textContent).toBe('1');
  });

  it('reads valid chapter from URL', () => {
    render(
      <MemoryRouter initialEntries={['/series/test?chapter=42']}>
        <ReaderProvider seriesId="test">
          <TestComponent />
        </ReaderProvider>
      </MemoryRouter>
    );
    expect(screen.getByTestId('chapter').textContent).toBe('42');
  });

  it('falls back to 1 if URL chapter is invalid', () => {
    render(
      <MemoryRouter initialEntries={['/series/test?chapter=invalid']}>
        <ReaderProvider seriesId="test">
          <TestComponent />
        </ReaderProvider>
      </MemoryRouter>
    );
    expect(screen.getByTestId('chapter').textContent).toBe('1');
  });

  it('updates URL when chapter is set', () => {
    render(
      <MemoryRouter initialEntries={['/series/test']}>
        <ReaderProvider seriesId="test">
          <TestComponent />
        </ReaderProvider>
      </MemoryRouter>
    );
    
    act(() => {
      screen.getByText('Set to 50').click();
    });
    
    expect(screen.getByTestId('chapter').textContent).toBe('50');
    expect(screen.getByTestId('url').textContent).toContain('?chapter=50');
  });

  it('ignores invalid negative chapter sets', () => {
    render(
      <MemoryRouter initialEntries={['/series/test?chapter=10']}>
        <ReaderProvider seriesId="test">
          <TestComponent />
        </ReaderProvider>
      </MemoryRouter>
    );
    
    act(() => {
      screen.getByText('Set Invalid').click();
    });
    
    // Should not change
    expect(screen.getByTestId('chapter').textContent).toBe('10');
  });
});
