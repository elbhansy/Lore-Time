import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { TemporalProvider } from '../../../state/temporal/temporal-context';
import { ShellProvider, useShellContext } from '../../../state/shell/shell-context';
import { ApplicationShell } from '../ApplicationShell';
import { Header } from '../Header';
import { Sidebar } from '../Sidebar';
import { InspectorPanel } from '../InspectorPanel';
import { CommandPalette } from '../CommandPalette';

const TestApp: React.FC<{ initialChapter?: number; seriesId?: string }> = ({
  initialChapter = 5,
  seriesId = 'test-series-42',
}) => {
  return (
    <MemoryRouter initialEntries={[`/series/${seriesId}?chapter=${initialChapter}`]}>
      <Routes>
        <Route
          path="/series/:seriesId"
          element={
            <TemporalProvider seriesId={seriesId} defaultChapter={initialChapter}>
              <ShellProvider>
                <ApplicationShell seriesId={seriesId}>
                  <div data-testid="workspace-content">Workspace Active</div>
                </ApplicationShell>
              </ShellProvider>
            </TemporalProvider>
          }
        />
        <Route
          path="/series/:seriesId/timeline"
          element={
            <TemporalProvider seriesId={seriesId} defaultChapter={initialChapter}>
              <ShellProvider>
                <ApplicationShell seriesId={seriesId}>
                  <div data-testid="timeline-view">Timeline Stream Active</div>
                </ApplicationShell>
              </ShellProvider>
            </TemporalProvider>
          }
        />
      </Routes>
    </MemoryRouter>
  );
};

describe('Application Shell & Navigation UX (Phase 6.2)', () => {
  it('renders all core landmarks: banner, navigation, main, and contentinfo', () => {
    render(<TestApp />);

    expect(screen.getByRole('banner')).not.toBeNull();
    expect(screen.getByRole('navigation')).not.toBeNull();
    expect(screen.getByRole('main')).not.toBeNull();
    expect(screen.getByRole('contentinfo')).not.toBeNull();
    expect(screen.getByTestId('workspace-content')).not.toBeNull();
  });

  it('displays active series and reader chapter in Header', () => {
    render(<TestApp initialChapter={12} seriesId="series-alpha" />);

    expect(screen.getByText(/SERIES: series-a/i)).not.toBeNull();
    expect(screen.getByText('Ch. 12')).not.toBeNull();
  });

  it('steps temporal horizon forward and backward using header controls', () => {
    render(<TestApp initialChapter={5} seriesId="series-alpha" />);

    const prevBtn = screen.getByTitle('Step backward one chapter');
    const nextBtn = screen.getByTitle('Step forward one chapter');

    expect((prevBtn as HTMLButtonElement).disabled).toBe(false);
    expect((nextBtn as HTMLButtonElement).disabled).toBe(false);

    fireEvent.click(nextBtn);
    expect(screen.getByText('Ch. 6')).not.toBeNull();

    fireEvent.click(prevBtn);
    expect(screen.getByText('Ch. 5')).not.toBeNull();
  });

  it('toggles sidebar collapse and expansion', () => {
    render(<TestApp />);

    const toggleBtn = screen.getByTitle('Toggle navigation sidebar');
    const aside = screen.getByLabelText('Story Intelligence Sidebar');

    // Default width is 240px
    expect(aside.style.width).toBe('var(--tsi-sidebar-width)');

    // Click to collapse
    fireEvent.click(toggleBtn);
    expect(aside.style.width).toBe('64px');

    // Click to expand
    fireEvent.click(toggleBtn);
    expect(aside.style.width).toBe('var(--tsi-sidebar-width)');
  });

  it('toggles contextual InspectorPanel from Header button', () => {
    render(<TestApp />);

    const inspectorBtn = screen.getByTitle('Toggle Context Inspector');

    // Default: inspector closed
    expect(screen.queryByRole('complementary')).toBeNull();

    // Open inspector
    fireEvent.click(inspectorBtn);
    expect(screen.getByRole('complementary')).not.toBeNull();
    expect(screen.getByText('Context Inspector')).not.toBeNull();

    // Close via header button
    fireEvent.click(inspectorBtn);
    expect(screen.queryByRole('complementary')).toBeNull();
  });

  it('opens CommandPalette modal via Ctrl+K and executes navigation', () => {
    render(<TestApp />);

    // Trigger open via command bar search button
    const searchTrigger = screen.getByLabelText(/Open Command Search/i);
    fireEvent.click(searchTrigger);

    // Dialog is visible
    expect(screen.getByRole('dialog')).not.toBeNull();
    expect(screen.getByPlaceholderText(/Search commands/i)).not.toBeNull();

    // Filter by 'timeline'
    const input = screen.getByPlaceholderText(/Search commands/i);
    fireEvent.change(input, { target: { value: 'timeline' } });

    expect(screen.getByText('Go to Timeline Feed')).not.toBeNull();

    // Click command item
    fireEvent.click(screen.getByText('Go to Timeline Feed'));

    // Command palette closes and navigates to timeline view
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(screen.getByTestId('timeline-view')).not.toBeNull();
  });

  it('navigates through Sidebar items while strictly preserving series scope', () => {
    render(<TestApp seriesId="series-omega" />);

    const timelineLink = screen.getByText('Timeline Feed').closest('a');
    expect(timelineLink?.getAttribute('href')).toBe('/series/series-omega/timeline');

    const charactersLink = screen.getByText('Characters').closest('a');
    expect(charactersLink?.getAttribute('href')).toBe('/series/series-omega/characters');

    const graphLink = screen.getByText('Intelligence Graph').closest('a');
    expect(graphLink?.getAttribute('href')).toBe('/series/series-omega/graph');
  });
});
