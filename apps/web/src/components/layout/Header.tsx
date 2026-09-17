import React, { ReactNode } from 'react';
import { useTemporalContext } from '../../state/temporal/temporal-context';
import { useShellContext } from '../../state/shell/shell-context';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export interface HeaderProps {
  title?: string;
  actions?: ReactNode;
}

export const Header: React.FC<HeaderProps> = ({
  title = 'Temporal Story Intelligence',
  actions,
}) => {
  const {
    readerChapter,
    seriesId,
    stepBackward,
    stepForward,
    canStepBackward,
    canStepForward,
    minVisibleChapter,
    maxVisibleChapter,
  } = useTemporalContext();

  const {
    toggleSidebar,
    isSidebarCollapsed,
    openCommandPalette,
    toggleInspector,
    isInspectorOpen,
  } = useShellContext();

  return (
    <header
      role="banner"
      style={{
        height: 'var(--tsi-header-height)',
        backgroundColor: 'var(--tsi-surface-primary)',
        borderBottom: '1px solid var(--tsi-border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--tsi-space-md)',
        flexShrink: 0,
        zIndex: 50,
      }}
    >
      {/* Left: Sidebar Toggle & Series Context */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--tsi-space-sm)' }}>
        <Button
          size="sm"
          variant="ghost"
          onClick={toggleSidebar}
          aria-label={isSidebarCollapsed ? 'Expand navigation sidebar' : 'Collapse navigation sidebar'}
          title="Toggle navigation sidebar"
          style={{ padding: '4px 8px', fontSize: '0.875rem' }}
        >
          ☰
        </Button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '1rem',
              fontWeight: 700,
              color: 'var(--tsi-text-primary)',
              letterSpacing: '-0.02em',
              whiteSpace: 'nowrap',
            }}
          >
            {title}
          </span>
          <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
            SERIES: {seriesId ? seriesId.slice(0, 8) : 'GLOBAL'}
          </Badge>
        </div>
      </div>

      {/* Center: Command Palette Trigger */}
      <div style={{ display: 'flex', alignItems: 'center', maxWidth: '320px', width: '100%', margin: '0 16px' }}>
        <button
          onClick={openCommandPalette}
          aria-label="Open Command Search (Ctrl+K)"
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--tsi-surface-secondary)',
            border: '1px solid var(--tsi-border-default)',
            borderRadius: 'var(--tsi-radius-md)',
            padding: '5px 12px',
            color: 'var(--tsi-text-muted)',
            fontSize: '0.8125rem',
            cursor: 'pointer',
            transition: 'border-color 0.15s ease',
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>🔍</span>
            <span>Search or jump to...</span>
          </span>
          <kbd
            style={{
              fontSize: '0.6875rem',
              backgroundColor: 'var(--tsi-surface-elevated)',
              padding: '1px 5px',
              borderRadius: 'var(--tsi-radius-xs)',
              border: '1px solid var(--tsi-border-subtle)',
              color: 'var(--tsi-text-secondary)',
            }}
          >
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right: Authoritative Temporal Horizon Controller & Inspector Toggle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--tsi-space-sm)' }}>
        <div
          role="region"
          aria-label="Temporal Horizon Controller"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--tsi-surface-secondary)',
            padding: '3px 8px',
            borderRadius: 'var(--tsi-radius-md)',
            border: '1px solid var(--tsi-border-default)',
          }}
        >
          <span
            style={{
              fontSize: '0.6875rem',
              color: 'var(--tsi-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Horizon:
          </span>

          <Badge
            variant="temporal"
            title={`Temporal Scope: Chapter ${minVisibleChapter} to ${maxVisibleChapter}. Future information beyond Chapter ${readerChapter} is excluded.`}
          >
            Ch. {readerChapter}
          </Badge>

          <div style={{ display: 'flex', gap: '2px' }}>
            <Button
              size="sm"
              variant="ghost"
              disabled={!canStepBackward}
              onClick={stepBackward}
              aria-label="Step backward one chapter"
              title="Step backward one chapter"
              style={{ padding: '2px 6px', fontSize: '0.75rem' }}
            >
              ◀
            </Button>
            <Button
              size="sm"
              variant="ghost"
              disabled={!canStepForward}
              onClick={stepForward}
              aria-label="Step forward one chapter"
              title="Step forward one chapter"
              style={{ padding: '2px 6px', fontSize: '0.75rem' }}
            >
              ▶
            </Button>
          </div>
        </div>

        {/* Inspector Toggle */}
        <Button
          size="sm"
          variant={isInspectorOpen ? 'primary' : 'secondary'}
          onClick={toggleInspector}
          aria-label={isInspectorOpen ? 'Close entity inspector panel' : 'Open entity inspector panel'}
          title="Toggle Context Inspector"
          style={{ padding: '4px 8px', fontSize: '0.8125rem' }}
        >
          {isInspectorOpen ? 'Inspector ◨' : 'Inspector ◧'}
        </Button>

        {actions}
      </div>
    </header>
  );
};
