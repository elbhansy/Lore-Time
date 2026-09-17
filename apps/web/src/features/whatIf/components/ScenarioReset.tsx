import React from 'react';

export interface ScenarioResetProps {
  onReset: () => void;
  disabled?: boolean;
}

export const ScenarioReset: React.FC<ScenarioResetProps> = ({ onReset, disabled = false }) => {
  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={onReset}
        disabled={disabled}
        data-testid="scenario-reset-btn"
        className="px-3 py-1.5 text-xs font-mono font-medium rounded-lg border border-border/50 bg-background/60 hover:bg-destructive/10 hover:border-destructive/40 text-muted-foreground hover:text-destructive transition-colors disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1.5"
        title="Reset scenario to canonical baseline (preserves current reader chapter)"
      >
        <span>↺</span>
        <span>Reset to Canon</span>
      </button>
    </div>
  );
};
