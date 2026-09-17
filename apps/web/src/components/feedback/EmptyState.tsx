import React, { ReactNode } from 'react';
import { Button } from '../ui/Button';

export interface EmptyStateProps {
  title: string;
  description: string;
  icon?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon = '∅',
  actionLabel,
  onAction,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--tsi-space-2xl) var(--tsi-space-lg)',
        textAlign: 'center',
        backgroundColor: 'var(--tsi-surface-primary)',
        border: '1px dashed var(--tsi-border-default)',
        borderRadius: 'var(--tsi-radius-lg)',
        maxWidth: '500px',
        margin: '0 auto',
      }}
    >
      <div
        style={{
          fontSize: '2rem',
          color: 'var(--tsi-text-muted)',
          marginBottom: 'var(--tsi-space-sm)',
        }}
      >
        {icon}
      </div>
      <h4
        style={{
          margin: '0 0 var(--tsi-space-xs)',
          fontSize: '1rem',
          fontWeight: 600,
          color: 'var(--tsi-text-primary)',
        }}
      >
        {title}
      </h4>
      <p
        style={{
          margin: '0 0 var(--tsi-space-md)',
          fontSize: '0.875rem',
          color: 'var(--tsi-text-secondary)',
          maxWidth: '380px',
        }}
      >
        {description}
      </p>
      {actionLabel && onAction && (
        <Button variant="secondary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
