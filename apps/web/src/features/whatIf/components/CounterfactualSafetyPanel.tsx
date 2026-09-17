import React from 'react';

export interface CounterfactualSafetyPanelProps {
  seriesId: string;
  readerChapter: number;
  scenarioChapter: number | null;
  isHypothetical: boolean;
  status: 'IDLE' | 'CONFIGURED' | 'EXECUTING' | 'SIMULATED';
}

export const CounterfactualSafetyPanel: React.FC<CounterfactualSafetyPanelProps> = ({
  seriesId,
  readerChapter,
  scenarioChapter,
  isHypothetical,
  status,
}) => {
  return (
    <div
      data-testid="counterfactual-safety-panel"
      className="p-4 rounded-xl border border-border/40 bg-card/40 backdrop-blur-sm space-y-4"
    >
      <div className="flex items-center justify-between pb-3 border-b border-border/30">
        <div className="flex items-center gap-2">
          <span className="text-primary text-sm">🛡️</span>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground/90">
            Temporal Safety & Sandbox Provenance
          </h3>
        </div>
        <span
          data-testid="sandbox-state-badge"
          className={`px-2 py-0.5 text-[10px] font-mono rounded border uppercase font-medium ${
            status === 'SIMULATED'
              ? 'bg-primary/20 text-primary border-primary/40'
              : 'bg-muted/40 text-muted-foreground border-border/40'
          }`}
        >
          {status}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        {/* Sourcing Boundary */}
        <div className="p-2.5 rounded-lg bg-background/50 border border-border/30 space-y-1">
          <div className="text-[10px] uppercase font-mono text-muted-foreground tracking-wider">
            Canonical Horizon
          </div>
          <div className="font-semibold text-foreground flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
            Chapter {readerChapter}
          </div>
          <div className="text-[10px] text-muted-foreground">
            Sourced strictly from confirmed story events.
          </div>
        </div>

        {/* Hypothetical Status */}
        <div className="p-2.5 rounded-lg bg-background/50 border border-border/30 space-y-1">
          <div className="text-[10px] uppercase font-mono text-muted-foreground tracking-wider">
            Simulation Status
          </div>
          <div className="font-semibold text-foreground flex items-center gap-1.5">
            <span
              className={`w-1.5 h-1.5 rounded-full inline-block ${
                isHypothetical ? 'bg-primary animate-pulse' : 'bg-muted-foreground'
              }`}
            />
            {isHypothetical ? 'HYPOTHETICAL (NOT CANON)' : 'CANONICAL BASELINE'}
          </div>
          <div className="text-[10px] text-muted-foreground">
            {isHypothetical
              ? 'Computed in ephemeral sandbox; non-authoritative.'
              : 'Baseline state matches published canon.'}
          </div>
        </div>

        {/* Persistence Isolation */}
        <div className="p-2.5 rounded-lg bg-background/50 border border-border/30 space-y-1">
          <div className="text-[10px] uppercase font-mono text-muted-foreground tracking-wider">
            Database Persistence
          </div>
          <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
            0 Mutations / Ephemeral
          </div>
          <div className="text-[10px] text-muted-foreground">
            PostgreSQL & canonical caches remain immutable.
          </div>
        </div>

        {/* Temporal Firewall */}
        <div className="p-2.5 rounded-lg bg-background/50 border border-border/30 space-y-1">
          <div className="text-[10px] uppercase font-mono text-muted-foreground tracking-wider">
            Firewall Boundary
          </div>
          <div className="font-semibold text-foreground flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-primary inline-block" />
            N+1 Blocked (Ch. &gt; {readerChapter})
          </div>
          <div className="text-[10px] text-muted-foreground">
            {scenarioChapter !== null && scenarioChapter > readerChapter
              ? 'VIOLATION: Scenario horizon exceeds reader chapter.'
              : 'Zero future information leakage guaranteed.'}
          </div>
        </div>
      </div>

      <div className="pt-2 text-[10px] text-muted-foreground flex flex-wrap items-center justify-between gap-2 border-t border-border/20">
        <div className="flex items-center gap-2">
          <span className="font-mono text-foreground/70">Series ID: {seriesId}</span>
          <span>•</span>
          <span>Single-source presentation model</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-emerald-400">
            <span>●</span> CANONICAL
          </span>
          <span className="flex items-center gap-1 text-primary">
            <span>●</span> HYPOTHETICAL
          </span>
          <span className="flex items-center gap-1 text-amber-400">
            <span>●</span> INFERENCE
          </span>
        </div>
      </div>
    </div>
  );
};
