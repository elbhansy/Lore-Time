import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useTemporalContext } from '../../state/temporal/temporal-context';
import { useShellContext } from '../../state/shell/shell-context';
import {
  useStoryGraph,
  useTimelineFeed,
  useTemporalComparison,
} from '../../features/temporal/queries/useIntelligenceQueries';
import {
  CounterfactualScenarioDTO,
  CounterfactualAssumption,
} from '../../api/contracts/read-models';
import {
  adaptHypotheticalImpacts,
  buildCounterfactualScenario,
  FormattedHypotheticalImpact,
} from '../../features/whatIf/whatIfAdapters';

import { WhatIfHeader } from '../../features/whatIf/components/WhatIfHeader';
import { CanonicalContextBar } from '../../features/whatIf/components/CanonicalContextBar';
import { ScenarioBuilder, TargetOption } from '../../features/whatIf/components/ScenarioBuilder';
import { ScenarioSummary } from '../../features/whatIf/components/ScenarioSummary';
import { CounterfactualExecutionState } from '../../features/whatIf/components/CounterfactualExecutionState';
import { CounterfactualComparison } from '../../features/whatIf/components/CounterfactualComparison';
import { HypotheticalImpactList } from '../../features/whatIf/components/HypotheticalImpactList';
import { CounterfactualSafetyPanel } from '../../features/whatIf/components/CounterfactualSafetyPanel';
import { ScenarioReset } from '../../features/whatIf/components/ScenarioReset';

export const WhatIfPage: React.FC = () => {
  const { seriesId: routeSeriesId } = useParams<{ seriesId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  const {
    seriesId: contextSeriesId,
    readerChapter,
    totalChapters = 200,
    stepForward,
    stepBackward,
    setReaderChapter,
    canStepForward,
    canStepBackward,
  } = useTemporalContext();

  const activeSeriesId = routeSeriesId || contextSeriesId;
  const { openInspector } = useShellContext();

  // URL ?chapter=N synchronization
  useEffect(() => {
    const chapterParam = searchParams.get('chapter');
    if (chapterParam) {
      const parsed = parseInt(chapterParam, 10);
      if (!isNaN(parsed) && parsed >= 1 && parsed !== readerChapter) {
        setReaderChapter(parsed);
      }
    }
  }, [searchParams, readerChapter, setReaderChapter]);

  const handleStepBackward = useCallback(() => {
    if (canStepBackward) {
      stepBackward();
      setSearchParams(
        (prev) => {
          const p = new URLSearchParams(prev);
          p.set('chapter', String(Math.max(1, readerChapter - 1)));
          return p;
        },
        { replace: true }
      );
    }
  }, [canStepBackward, stepBackward, readerChapter, setSearchParams]);

  const handleStepForward = useCallback(() => {
    if (canStepForward) {
      stepForward();
      setSearchParams(
        (prev) => {
          const p = new URLSearchParams(prev);
          p.set('chapter', String(Math.min(totalChapters, readerChapter + 1)));
          return p;
        },
        { replace: true }
      );
    }
  }, [canStepForward, stepForward, readerChapter, totalChapters, setSearchParams]);

  // Lightweight discovery for interventions (Zero N+1: uses cached read models)
  const timelineQuery = useTimelineFeed(
    activeSeriesId,
    readerChapter,
    { from: 1, to: readerChapter, limit: 100 },
    true
  );

  const characterGraphQuery = useStoryGraph(
    activeSeriesId,
    readerChapter,
    'relationship',
    true
  );

  const availableTargets: TargetOption[] = useMemo(() => {
    const targets: TargetOption[] = [];

    // Characters from graph
    const nodes = characterGraphQuery.data?.nodes || [];
    nodes.forEach((n) => {
      targets.push({
        id: n.id,
        name: n.label,
        type: 'CHARACTER',
        chapter: n.chapter ?? undefined,
      });
    });

    // Events from timeline
    const events = timelineQuery.data?.events || [];
    events
      .filter((e) => e.chapter_number <= readerChapter)
      .forEach((e) => {
        targets.push({
          id: e.event_id,
          name: e.title || `Event ${e.event_id}`,
          type: 'EVENT',
          chapter: e.chapter_number,
        });
      });

    return targets;
  }, [characterGraphQuery.data?.nodes, timelineQuery.data?.events, readerChapter]);

  // Active simulated scenario state
  const [activeScenario, setActiveScenario] = useState<CounterfactualScenarioDTO | null>(null);

  // TEMPORAL FIREWALL DEFENSE:
  // If reader navigates backward and current scenario's intervention exceeds readerChapter,
  // purely derive null to prevent stale future information leakage without triggering cascading renders.
  const effectiveActiveScenario = useMemo(() => {
    if (!activeScenario) return null;
    if (
      activeScenario.assumption.target_chapter > readerChapter ||
      activeScenario.reader_chapter > readerChapter
    ) {
      return null;
    }
    return activeScenario;
  }, [activeScenario, readerChapter]);

  // Counterfactual Query / Simulation execution
  // Uses backend comparison endpoint: GET /series/{series_id}/comparison
  const fromChapter = effectiveActiveScenario ? Math.max(1, effectiveActiveScenario.assumption.target_chapter - 1) : 1;
  const toChapter = effectiveActiveScenario ? effectiveActiveScenario.reader_chapter : readerChapter;

  const comparisonQuery = useTemporalComparison(
    activeSeriesId,
    fromChapter,
    toChapter,
    readerChapter,
    !!effectiveActiveScenario
  );

  const isSimulating = comparisonQuery.isFetching;

  const handleExecuteScenario = useCallback(
    (assumption: CounterfactualAssumption) => {
      const scenario = buildCounterfactualScenario(
        activeSeriesId,
        readerChapter,
        assumption,
        comparisonQuery.data || null
      );
      setActiveScenario(scenario);
    },
    [activeSeriesId, readerChapter, comparisonQuery.data]
  );

  const handleResetScenario = useCallback(() => {
    setActiveScenario(null);
  }, []);

  // Extract adapted impacts
  const hypotheticalImpacts = useMemo(() => {
    if (!effectiveActiveScenario || !comparisonQuery.data) return [];
    return adaptHypotheticalImpacts(comparisonQuery.data, effectiveActiveScenario);
  }, [effectiveActiveScenario, comparisonQuery.data]);

  // Inspector inspection for targeted entity
  const handleInspectEntity = useCallback(
    (impact: FormattedHypotheticalImpact) => {
      openInspector({
        title: `Hypothetical Impact: ${impact.entityName}`,
        subtitle: `Intervention at Chapter ${effectiveActiveScenario?.assumption.target_chapter || readerChapter}`,
        badge: {
          label: 'HYPOTHETICAL SIMULATION',
          variant: 'warning',
        },
        content: (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-lg border border-primary/30 bg-primary/10">
              <div className="font-mono text-[10px] uppercase tracking-wider text-primary font-bold">
                Simulation Delta
              </div>
              <div className="mt-1 font-semibold text-foreground text-sm">
                {impact.entityName} ({impact.entityType})
              </div>
              <div className="mt-2 text-muted-foreground">
                Changed Property: <span className="font-mono text-foreground">{impact.changedProperty}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="p-2 rounded bg-background/50 border border-border/40">
                <div className="text-[10px] text-muted-foreground uppercase font-mono">Canonical</div>
                <div className="mt-1 font-mono text-emerald-400 font-semibold">{impact.canonicalValue}</div>
              </div>
              <div className="p-2 rounded bg-background/50 border border-border/40">
                <div className="text-[10px] text-muted-foreground uppercase font-mono">Hypothetical</div>
                <div className="mt-1 font-mono text-primary font-bold">{impact.hypotheticalValue}</div>
              </div>
            </div>

            <div className="text-[10px] text-muted-foreground italic">
              Note: This hypothetical projection is ephemeral and does not mutate canonical lore.
            </div>
          </div>
        ),
      });
    },
    [effectiveActiveScenario, readerChapter, openInspector]
  );

  const scenarioChapter = effectiveActiveScenario ? effectiveActiveScenario.assumption.target_chapter : null;
  const currentStatus = effectiveActiveScenario
    ? isSimulating
      ? 'EXECUTING'
      : comparisonQuery.isError
      ? 'CONFIGURED'
      : 'SIMULATED'
    : 'IDLE';

  return (
    <div
      data-testid="what-if-page"
      className="flex flex-col min-h-full space-y-6 pb-12 animate-in fade-in duration-200"
    >
      {/* Workspace Header */}
      <WhatIfHeader
        seriesId={activeSeriesId}
        readerChapter={readerChapter}
        totalChapters={totalChapters}
        isSimulating={isSimulating}
        onStepBackward={handleStepBackward}
        onStepForward={handleStepForward}
        canStepBackward={canStepBackward}
        canStepForward={canStepForward}
      />

      {/* Canonical Context Baseline */}
      <CanonicalContextBar
        seriesId={activeSeriesId}
        readerChapter={readerChapter}
        totalCharactersVisible={availableTargets.filter((t) => t.type === 'CHARACTER').length}
        totalEventsVisible={availableTargets.filter((t) => t.type === 'EVENT').length}
      />

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Scenario Builder & Summary */}
        <div className="lg:col-span-5 space-y-5">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground uppercase tracking-wider flex items-center gap-2">
                <span>⚡</span>
                <span>Intervention Builder</span>
              </h2>
              {effectiveActiveScenario && (
                <ScenarioReset onReset={handleResetScenario} disabled={isSimulating} />
              )}
            </div>

            <ScenarioBuilder
              readerChapter={readerChapter}
              availableTargets={availableTargets}
              onExecuteScenario={handleExecuteScenario}
              isExecuting={isSimulating}
            />
          </div>

          {/* Scenario Transition Summary */}
          <ScenarioSummary
            scenario={effectiveActiveScenario}
            readerChapter={readerChapter}
          />
        </div>

        {/* Right Column: Execution State & Hypothetical Results */}
        <div className="lg:col-span-7 space-y-5">
          {/* Loading / Error States */}
          {isSimulating && (
            <CounterfactualExecutionState
              status="executing"
            />
          )}

          {comparisonQuery.isError && (
            <CounterfactualExecutionState
              status="error"
              errorMessage={
                comparisonQuery.error instanceof Error
                  ? comparisonQuery.error.message
                  : 'Failed to compute counterfactual simulation.'
              }
            />
          )}

          {/* Simulated Results View */}
          {effectiveActiveScenario && !isSimulating && comparisonQuery.data && (
            <div className="space-y-5">
              {/* Comparative Metrics */}
              <CounterfactualComparison
                divergence={comparisonQuery.data}
                readerChapter={readerChapter}
              />

              {/* Impacted Entities List */}
              <HypotheticalImpactList
                impacts={hypotheticalImpacts}
                onInspectEntity={handleInspectEntity}
              />
            </div>
          )}

          {/* Empty State when no scenario executed */}
          {!effectiveActiveScenario && !isSimulating && (
            <div
              data-testid="what-if-empty-state"
              className="p-8 rounded-xl border border-dashed border-border/50 bg-card/30 flex flex-col items-center justify-center text-center space-y-3 min-h-[300px]"
            >
              <span className="text-3xl">⑂</span>
              <div className="font-semibold text-foreground text-sm">
                No Active Counterfactual Simulation
              </div>
              <p className="text-xs text-muted-foreground max-w-sm">
                Select an entity or event from Chapter 1 to {readerChapter}, configure a hypothetical
                intervention, and click "Run What-If Simulation ↯" to simulate divergence.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Temporal Safety & Provenance Panel */}
      <CounterfactualSafetyPanel
        seriesId={activeSeriesId}
        readerChapter={readerChapter}
        scenarioChapter={scenarioChapter}
        isHypothetical={!!effectiveActiveScenario}
        status={currentStatus}
      />
    </div>
  );
};
