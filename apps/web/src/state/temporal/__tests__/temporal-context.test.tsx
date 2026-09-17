import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { TemporalProvider, useTemporalContext } from '../temporal-context';

const ConsumerComponent: React.FC = () => {
  const {
    seriesId,
    readerChapter,
    minVisibleChapter,
    maxVisibleChapter,
    stepForward,
    stepBackward,
    canStepForward,
    canStepBackward,
  } = useTemporalContext();

  return (
    <div>
      <div data-testid="series-id">{seriesId}</div>
      <div data-testid="reader-chapter">{readerChapter}</div>
      <div data-testid="temporal-range">{`${minVisibleChapter}..${maxVisibleChapter}`}</div>
      <div data-testid="can-forward">{canStepForward ? 'yes' : 'no'}</div>
      <div data-testid="can-backward">{canStepBackward ? 'yes' : 'no'}</div>
      <button onClick={stepForward}>Step Forward</button>
      <button onClick={stepBackward}>Step Backward</button>
    </div>
  );
};

describe('TemporalContext State & Provider', () => {
  it('initializes with default chapter 1 and maintains strict horizon boundary', () => {
    render(
      <MemoryRouter initialEntries={['/series/test-series-123']}>
        <TemporalProvider seriesId="test-series-123" totalChapters={50}>
          <ConsumerComponent />
        </TemporalProvider>
      </MemoryRouter>
    );

    expect(screen.getByTestId('series-id').textContent).toBe('test-series-123');
    expect(screen.getByTestId('reader-chapter').textContent).toBe('1');
    expect(screen.getByTestId('temporal-range').textContent).toBe('1..1');
    expect(screen.getByTestId('can-backward').textContent).toBe('no');
    expect(screen.getByTestId('can-forward').textContent).toBe('yes');
  });

  it('reads reader chapter from URL query parameter correctly', () => {
    render(
      <MemoryRouter initialEntries={['/series/test-series-123?chapter=15']}>
        <TemporalProvider seriesId="test-series-123" totalChapters={50}>
          <ConsumerComponent />
        </TemporalProvider>
      </MemoryRouter>
    );

    expect(screen.getByTestId('reader-chapter').textContent).toBe('15');
    expect(screen.getByTestId('temporal-range').textContent).toBe('1..15');
    expect(screen.getByTestId('can-backward').textContent).toBe('yes');
    expect(screen.getByTestId('can-forward').textContent).toBe('yes');
  });

  it('clamps invalid or out-of-range chapters to safe temporal bounds', () => {
    render(
      <MemoryRouter initialEntries={['/series/test-series-123?chapter=999']}>
        <TemporalProvider seriesId="test-series-123" totalChapters={50}>
          <ConsumerComponent />
        </TemporalProvider>
      </MemoryRouter>
    );

    // Clamped to totalChapters (50)
    expect(screen.getByTestId('reader-chapter').textContent).toBe('50');
    expect(screen.getByTestId('can-forward').textContent).toBe('no');
    expect(screen.getByTestId('can-backward').textContent).toBe('yes');
  });
});
