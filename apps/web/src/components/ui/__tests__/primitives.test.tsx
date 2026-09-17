import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Button } from '../Button';
import { Badge } from '../Badge';
import { Card } from '../Card';
import { EmptyState } from '../../feedback/EmptyState';
import { ErrorState } from '../../feedback/ErrorState';

describe('UI Primitives and Design System', () => {
  it('renders Button with variants and handles loading state', () => {
    const { rerender } = render(<Button variant="primary">Investigate</Button>);
    expect(screen.getByRole('button').textContent).toContain('Investigate');

    rerender(<Button isLoading>Investigate</Button>);
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole('button').textContent).toContain('⟳');
  });

  it('renders Badge with semantic and temporal variants', () => {
    render(
      <div>
        <Badge variant="temporal">Ch. 42</Badge>
        <Badge variant="success">Resolved</Badge>
      </div>
    );
    expect(screen.getByText('Ch. 42')).not.toBeNull();
    expect(screen.getByText('Resolved')).not.toBeNull();
  });

  it('renders Card with content', () => {
    render(<Card>Story Horizon Card</Card>);
    expect(screen.getByText('Story Horizon Card')).not.toBeNull();
  });

  it('renders EmptyState without error styling', () => {
    render(
      <EmptyState
        title="No Causal Chains Found"
        description="No events initiated upstream causality at this chapter."
      />
    );
    expect(screen.getByText('No Causal Chains Found')).not.toBeNull();
    expect(screen.getByText(/No events initiated upstream/)).not.toBeNull();
  });

  it('renders ErrorState with status code and retry action', () => {
    let retried = false;
    render(
      <ErrorState
        title="Backend Timeout"
        message="Could not reach intelligence core."
        status={504}
        onRetry={() => { retried = true; }}
      />
    );
    expect(screen.getByText('Backend Timeout (504)')).not.toBeNull();
    expect(screen.getByText('Retry Query')).not.toBeNull();
    screen.getByText('Retry Query').click();
    expect(retried).toBe(true);
  });
});
