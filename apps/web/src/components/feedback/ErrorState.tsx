import React from 'react';
import { Button } from '../ui/Button';

export interface ErrorStateProps {
  title?: string;
  message: string;
  status?: number;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to Load Intelligence',
  message,
  status,
  onRetry,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--tsi-space-xl)',
        textAlign: 'center',
        backgroundColor: 'var(--tsi-surface-primary)',
        border: '1px solid var(--tsi-status-error-bg)',
        borderLeft: '4px solid var(--tsi-status-error)',
        borderRadius: 'var(--tsi-radius-md)',
        maxWidth: '560px',
        margin: 'var(--tsi-space-md) auto',
      }}
    >
      <div style={{ fontSize: '1.5rem', color: 'var(--tsi-status-error)', marginBottom: '8px' }}>
        ⚠
      </div>
      <h4 style={{ margin: '0 0 6px', fontSize: '1rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
        {title} {status ? `(${status})` : ''}
      </h4>
      <p style={{ margin: '0 0 16px', fontSize: '0.875rem', color: 'var(--tsi-text-secondary)', maxWidth: '420px' }}>
        {message}
      </p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Retry Query
        </Button>
      )}
    </div>
  );
};
