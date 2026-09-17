import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ErrorState } from '../feedback/ErrorState';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class GlobalErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[TSI GlobalErrorBoundary caught error]:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 'var(--tsi-space-2xl)', display: 'flex', justifyContent: 'center' }}>
          <ErrorState
            title={this.props.fallbackTitle || 'A rendering error occurred'}
            message={this.state.error?.message || 'An unexpected client error halted the view.'}
            onRetry={() => this.setState({ hasError: false, error: undefined })}
          />
        </div>
      );
    }

    return this.props.children;
  }
}
