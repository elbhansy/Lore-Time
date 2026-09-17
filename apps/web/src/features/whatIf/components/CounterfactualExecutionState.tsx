import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Skeleton } from '../../../components/feedback/Skeleton';
import { ErrorState } from '../../../components/feedback/ErrorState';

export type WhatIfStatus =
  | 'idle'
  | 'executing'
  | 'success'
  | 'error';

export interface CounterfactualExecutionStateProps {
  status: WhatIfStatus;
  errorMessage?: string | null;
  onRetry?: () => void;
}

export const CounterfactualExecutionState: React.FC<CounterfactualExecutionStateProps> = ({
  status,
  errorMessage,
  onRetry,
}) => {
  if (status === 'executing') {
    return (
      <Card style={{ display: 'flex', flexDirection: 'column', gap: '14px', padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--tsi-status-warning)' }}>
            Simulating In-Memory Counterfactual Sandbox...
          </span>
        </div>
        <Skeleton height={36} borderRadius="var(--tsi-radius-md)" />
        <Skeleton height={120} borderRadius="var(--tsi-radius-md)" />
      </Card>
    );
  }

  if (status === 'error') {
    return (
      <ErrorState
        title="Simulation Sandbox Execution Failed"
        message={errorMessage || 'An error occurred while evaluating hypothetical divergence.'}
        onRetry={onRetry}
      />
    );
  }

  return null;
};
