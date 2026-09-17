import React, { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { InspectorPanel } from './InspectorPanel';
import { CommandPalette } from './CommandPalette';
import { GlobalErrorBoundary } from '../feedback/GlobalErrorBoundary';
import { useTemporalContext } from '../../state/temporal/temporal-context';

export interface ApplicationShellProps {
  seriesId: string;
  inspector?: ReactNode;
  children: ReactNode;
  headerActions?: ReactNode;
}

export const ApplicationShell: React.FC<ApplicationShellProps> = ({
  seriesId,
  inspector,
  children,
  headerActions,
}) => {
  const { minVisibleChapter, maxVisibleChapter } = useTemporalContext();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: '100vw',
        height: '100vh',
        overflow: 'hidden',
        backgroundColor: 'var(--tsi-canvas)',
      }}
    >
      {/* Global Application Header */}
      <Header actions={headerActions} />

      {/* Main Structural Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Navigation Sidebar */}
        <Sidebar seriesId={seriesId} />

        {/* Main Workspace Stage */}
        <main
          role="main"
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto',
            backgroundColor: 'var(--tsi-canvas)',
            position: 'relative',
          }}
        >
          <GlobalErrorBoundary>
            {children}
          </GlobalErrorBoundary>
        </main>

        {/* Context Inspector Dock */}
        <GlobalErrorBoundary fallbackTitle="Inspector Error">
          {inspector || <InspectorPanel />}
        </GlobalErrorBoundary>
      </div>

      {/* Global Command Palette Modal */}
      <CommandPalette />

      {/* System Status Bar */}
      <footer
        role="contentinfo"
        style={{
          height: 'var(--tsi-systembar-height)',
          backgroundColor: 'var(--tsi-surface-primary)',
          borderTop: '1px solid var(--tsi-border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          fontSize: '0.6875rem',
          color: 'var(--tsi-text-muted)',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--tsi-status-success)' }} />
            <span>Core Connected</span>
          </span>
          <span>|</span>
          <span>Reader Scope: Ch. {minVisibleChapter}–{maxVisibleChapter} (Strict Firewall)</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span>Press <kbd style={{ background: 'var(--tsi-surface-elevated)', padding: '1px 4px', borderRadius: '2px', border: '1px solid var(--tsi-border-subtle)' }}>⌘K</kbd> for Commands</span>
          <span>|</span>
          <span>Deterministic Narrative Synthesis</span>
        </div>
      </footer>
    </div>
  );
};
