import React, { ReactNode } from 'react';
import { useShellContext } from '../../state/shell/shell-context';
import { Badge } from '../ui/Badge';

export interface InspectorPanelProps {
  title?: string;
  subtitle?: string;
  badge?: {
    label: string;
    variant?: 'default' | 'neutral' | 'success' | 'warning' | 'error' | 'temporal';
  };
  isOpen?: boolean;
  onClose?: () => void;
  children?: ReactNode;
}

export const InspectorPanel: React.FC<InspectorPanelProps> = ({
  title: propTitle,
  subtitle: propSubtitle,
  badge: propBadge,
  isOpen: propIsOpen,
  onClose: propOnClose,
  children: propChildren,
}) => {
  const { isInspectorOpen, inspectorPayload, closeInspector } = useShellContext();

  // Resolve controlled vs context props
  const open = propIsOpen !== undefined ? propIsOpen : isInspectorOpen;
  const title = propTitle || inspectorPayload?.title || 'Context Inspector';
  const subtitle = propSubtitle || inspectorPayload?.subtitle;
  const badge = propBadge || inspectorPayload?.badge;
  const content = propChildren || inspectorPayload?.content;
  const handleClose = propOnClose || closeInspector;

  if (!open) return null;

  return (
    <aside
      role="complementary"
      aria-label="Story Intelligence Inspector"
      style={{
        width: 'var(--tsi-inspector-width)',
        backgroundColor: 'var(--tsi-surface-primary)',
        borderLeft: '1px solid var(--tsi-border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        overflowY: 'auto',
        animation: 'inspector-slide 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--tsi-border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{
                fontSize: '0.8125rem',
                fontWeight: 600,
                color: 'var(--tsi-text-primary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {title}
            </span>
            {badge && (
              <Badge variant={badge.variant || 'neutral'} style={{ fontSize: '0.6875rem' }}>
                {badge.label}
              </Badge>
            )}
          </div>
          {subtitle && (
            <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {subtitle}
            </span>
          )}
        </div>

        <button
          onClick={handleClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--tsi-text-muted)',
            cursor: 'pointer',
            fontSize: '1rem',
            padding: '2px 6px',
            borderRadius: 'var(--tsi-radius-sm)',
            transition: 'color 0.15s ease',
          }}
          aria-label="Close Inspector"
          title="Close Inspector"
        >
          ✕
        </button>
      </div>

      {/* Content Body */}
      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
        {content ? (
          content
        ) : (
          <div
            style={{
              padding: '32px 16px',
              textAlign: 'center',
              color: 'var(--tsi-text-muted)',
              fontSize: '0.875rem',
            }}
          >
            Select an event, character, or node in the workspace to inspect detailed causal evidence and narrative provenance.
          </div>
        )}
      </div>
    </aside>
  );
};
