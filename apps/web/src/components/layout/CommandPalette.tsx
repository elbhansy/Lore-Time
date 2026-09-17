import React, { useEffect, useRef, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTemporalContext } from '../../state/temporal/temporal-context';
import { useShellContext } from '../../state/shell/shell-context';
import { Badge } from '../ui/Badge';

export interface CommandItem {
  id: string;
  category: 'Navigation' | 'Temporal' | 'Investigation';
  title: string;
  subtitle?: string;
  badge?: string;
  onSelect: () => void;
}

export const CommandPalette: React.FC = () => {
  const { isCommandPaletteOpen, closeCommandPalette } = useShellContext();
  const { seriesId, readerChapter, totalChapters = 200, stepForward, stepBackward, setReaderChapter } = useTemporalContext();
  const navigate = useNavigate();

  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global keyboard shortcut: Ctrl+K / Cmd+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isCommandPaletteOpen) {
          closeCommandPalette();
        } else {
          // Open via shell context
          // Note: can also call useShellContext().openCommandPalette()
          // but we listen to window events
          window.dispatchEvent(new CustomEvent('toggle-command-palette'));
        }
      } else if (e.key === 'Escape' && isCommandPaletteOpen) {
        e.preventDefault();
        closeCommandPalette();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isCommandPaletteOpen, closeCommandPalette]);

  // Focus input on open
  useEffect(() => {
    if (isCommandPaletteOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isCommandPaletteOpen]);

  // Command items definition
  const commands: CommandItem[] = useMemo(() => [
    {
      id: 'nav-overview',
      category: 'Navigation',
      title: 'Go to Story Overview',
      subtitle: 'High-level narrative dashboard and milestone summary',
      badge: 'View',
      onSelect: () => {
        navigate(`/series/${seriesId}`);
        closeCommandPalette();
      },
    },
    {
      id: 'nav-timeline',
      category: 'Navigation',
      title: 'Go to Timeline Feed',
      subtitle: 'Chronological events stream within current reader horizon',
      badge: 'Feed',
      onSelect: () => {
        navigate(`/series/${seriesId}/timeline`);
        closeCommandPalette();
      },
    },
    {
      id: 'nav-characters',
      category: 'Navigation',
      title: 'Go to Character Intelligence',
      subtitle: 'Profiles, status, and state transitions at current horizon',
      badge: 'Entities',
      onSelect: () => {
        navigate(`/series/${seriesId}/characters`);
        closeCommandPalette();
      },
    },
    {
      id: 'nav-graph',
      category: 'Navigation',
      title: 'Go to Intelligence Graph',
      subtitle: 'Network topology and relationship projections',
      badge: 'Visualizer',
      onSelect: () => {
        navigate(`/series/${seriesId}/graph`);
        closeCommandPalette();
      },
    },
    {
      id: 'nav-causality',
      category: 'Navigation',
      title: 'Go to Causal Chains',
      subtitle: 'Deterministic cause-and-effect paths and turning points',
      badge: 'Synthesis',
      onSelect: () => {
        navigate(`/series/${seriesId}/causality`);
        closeCommandPalette();
      },
    },
    {
      id: 'temporal-next',
      category: 'Temporal',
      title: `Step Forward to Chapter ${Math.min(readerChapter + 1, totalChapters)}`,
      subtitle: 'Advance reader temporal horizon boundary by +1 chapter',
      badge: 'Time',
      onSelect: () => {
        stepForward();
        closeCommandPalette();
      },
    },
    {
      id: 'temporal-prev',
      category: 'Temporal',
      title: `Step Backward to Chapter ${Math.max(readerChapter - 1, 1)}`,
      subtitle: 'Retract reader temporal horizon boundary by -1 chapter',
      badge: 'Time',
      onSelect: () => {
        stepBackward();
        closeCommandPalette();
      },
    },
    {
      id: 'temporal-start',
      category: 'Temporal',
      title: 'Reset to Chapter 1 (Genesis)',
      subtitle: 'Set reader boundary to origin chapter',
      badge: 'Reset',
      onSelect: () => {
        setReaderChapter(1);
        closeCommandPalette();
      },
    },
  ], [seriesId, readerChapter, totalChapters, navigate, closeCommandPalette, stepForward, stepBackward, setReaderChapter]);

  // Filter commands by query
  const filteredCommands = useMemo(() => {
    if (!query.trim()) return commands;
    const lower = query.toLowerCase();
    return commands.filter(
      (cmd) =>
        cmd.title.toLowerCase().includes(lower) ||
        (cmd.subtitle && cmd.subtitle.toLowerCase().includes(lower)) ||
        cmd.category.toLowerCase().includes(lower)
    );
  }, [commands, query]);

  // Keyboard navigation within list
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % (filteredCommands.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % (filteredCommands.length || 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredCommands[selectedIndex]) {
        filteredCommands[selectedIndex].onSelect();
      }
    }
  };

  if (!isCommandPaletteOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Story Command Palette"
      onClick={closeCommandPalette}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'var(--tsi-surface-overlay)',
        backdropFilter: 'blur(3px)',
        zIndex: 100,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start',
        paddingTop: '15vh',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '580px',
          backgroundColor: 'var(--tsi-surface-primary)',
          border: '1px solid var(--tsi-border-default)',
          borderRadius: 'var(--tsi-radius-lg)',
          boxShadow: 'var(--tsi-shadow-lg)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          animation: 'palette-scale 0.15s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        {/* Search Input */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderBottom: '1px solid var(--tsi-border-subtle)',
          }}
        >
          <span style={{ fontSize: '1rem', color: 'var(--tsi-accent-primary)' }}>⌘</span>
          <input
            ref={inputRef}
            type="text"
            role="combobox"
            aria-expanded="true"
            aria-controls="command-palette-results"
            placeholder="Search commands, navigation, or temporal actions..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            style={{
              flex: 1,
              backgroundColor: 'transparent',
              border: 'none',
              color: 'var(--tsi-text-primary)',
              fontSize: '0.9375rem',
              outline: 'none',
              fontFamily: 'inherit',
            }}
          />
          <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>ESC</Badge>
        </div>

        {/* Results List */}
        <div
          id="command-palette-results"
          role="listbox"
          style={{
            maxHeight: '340px',
            overflowY: 'auto',
            padding: '6px',
            display: 'flex',
            flexDirection: 'column',
            gap: '2px',
          }}
        >
          {filteredCommands.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--tsi-text-muted)', fontSize: '0.875rem' }}>
              No matching commands or actions.
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={cmd.id}
                  role="option"
                  aria-selected={isSelected}
                  onClick={cmd.onSelect}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: 'var(--tsi-radius-md)',
                    backgroundColor: isSelected ? 'var(--tsi-surface-elevated)' : 'transparent',
                    borderLeft: isSelected ? '3px solid var(--tsi-accent-primary)' : '3px solid transparent',
                    cursor: 'pointer',
                    transition: 'all 0.1s ease',
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <span
                      style={{
                        fontSize: '0.875rem',
                        fontWeight: isSelected ? 600 : 400,
                        color: isSelected ? 'var(--tsi-text-primary)' : 'var(--tsi-text-secondary)',
                      }}
                    >
                      {cmd.title}
                    </span>
                    {cmd.subtitle && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
                        {cmd.subtitle}
                      </span>
                    )}
                  </div>
                  {cmd.badge && (
                    <Badge variant={isSelected ? 'temporal' : 'neutral'} style={{ fontSize: '0.6875rem' }}>
                      {cmd.badge}
                    </Badge>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Palette Footer */}
        <div
          style={{
            padding: '8px 16px',
            borderTop: '1px solid var(--tsi-border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.75rem',
            color: 'var(--tsi-text-muted)',
            backgroundColor: 'var(--tsi-surface-secondary)',
          }}
        >
          <span>Use <kbd>↑</kbd> <kbd>↓</kbd> to navigate</span>
          <span><kbd>Enter</kbd> to select</span>
        </div>
      </div>
    </div>
  );
};
