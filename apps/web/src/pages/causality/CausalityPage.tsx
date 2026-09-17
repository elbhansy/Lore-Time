import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  Node,
  NodeMouseHandler,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  useStoryGraph,
  useTimelineFeed,
  useEventNarrativeExplanation,
  useCharacterNarrativeCausality,
} from '../../features/temporal/queries/useIntelligenceQueries';
import { useTemporalContext } from '../../state/temporal/temporal-context';
import { useShellContext } from '../../state/shell/shell-context';

import { CausalityHeader } from '../../features/causality/components/CausalityHeader';
import { CausalNode } from '../../features/causality/components/CausalNode';
import { CausalLegend } from '../../features/causality/components/CausalLegend';
import {
  CausalInvestigationControls,
  DiscoveryItem,
} from '../../features/causality/components/CausalInvestigationControls';
import { CausalSelectionSummary } from '../../features/causality/components/CausalSelectionSummary';
import {
  adaptCausalGraph,
  adaptNarrativeCausalSteps,
} from '../../features/causality/utils/causalAdapters';

import { Skeleton } from '../../components/feedback/Skeleton';
import { ErrorState } from '../../components/feedback/ErrorState';
import { EmptyState } from '../../components/feedback/EmptyState';
import { Badge } from '../../components/ui/Badge';

const nodeTypes = {
  causalNode: CausalNode,
};

export const CausalityPage: React.FC = () => {
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

  // Mode: EVENT or CHARACTER
  const initialMode = (searchParams.get('mode')?.toUpperCase() as 'EVENT' | 'CHARACTER') || 'EVENT';
  const [mode, setMode] = useState<'EVENT' | 'CHARACTER'>(initialMode);

  // Selected Target ID (Event or Character)
  const initialTargetId = searchParams.get('targetId') || null;
  const [selectedTargetId, setSelectedTargetId] = useState<string | null>(initialTargetId);

  // Search query for local filtering over discovery list
  const [searchQuery, setSearchQuery] = useState('');

  // Selected Causal Step in path view
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);

  // Sync URL ?chapter=N to TemporalContext
  useEffect(() => {
    const chapterParam = searchParams.get('chapter');
    if (chapterParam) {
      const parsed = parseInt(chapterParam, 10);
      if (!isNaN(parsed) && parsed >= 1 && parsed !== readerChapter) {
        setReaderChapter(parsed);
      }
    }
  }, [searchParams, readerChapter, setReaderChapter]);

  // Handle temporal navigation and keep URL in sync
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

  const handleJumpToStart = useCallback(() => {
    setReaderChapter(1);
    setSearchParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        p.set('chapter', '1');
        return p;
      },
      { replace: true }
    );
  }, [setReaderChapter, setSearchParams]);

  const handleJumpToHorizon = useCallback(() => {
    setReaderChapter(totalChapters);
    setSearchParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        p.set('chapter', String(totalChapters));
        return p;
      },
      { replace: true }
    );
  }, [setReaderChapter, totalChapters, setSearchParams]);

  // Mode switching with cross-target isolation (clean state wipe per direct rule)
  const handleModeChange = useCallback(
    (newMode: 'EVENT' | 'CHARACTER') => {
      setMode(newMode);
      setSelectedTargetId(null);
      setSelectedStepId(null);
      setSearchQuery('');
      setSearchParams(
        (prev) => {
          const p = new URLSearchParams(prev);
          p.set('mode', newMode.toLowerCase());
          p.delete('targetId');
          return p;
        },
        { replace: true }
      );
    },
    [setSearchParams]
  );

  const handleSelectTarget = useCallback(
    (targetId: string) => {
      const val = targetId || null;
      setSelectedTargetId(val);
      setSelectedStepId(null);
      setSearchParams(
        (prev) => {
          const p = new URLSearchParams(prev);
          if (val) {
            p.set('targetId', val);
          } else {
            p.delete('targetId');
          }
          return p;
        },
        { replace: true }
      );
    },
    [setSearchParams]
  );

  // 1. Lightweight Discovery Layer (Zero N+1: Timeline Feed for events, Character Graph for characters)
  const timelineDiscoveryQuery = useTimelineFeed(
    activeSeriesId,
    readerChapter,
    { from: 1, to: readerChapter, limit: 100 },
    mode === 'EVENT'
  );

  const characterDiscoveryQuery = useStoryGraph(
    activeSeriesId,
    readerChapter,
    'relationship',
    mode === 'CHARACTER'
  );

  // Build discovery list bounded by readerChapter
  const discoveryItems: DiscoveryItem[] = useMemo(() => {
    if (mode === 'EVENT') {
      const events = timelineDiscoveryQuery.data?.events || [];
      return events
        .filter((e) => e.chapter_number <= readerChapter)
        .map((e) => ({
          id: e.event_id,
          label: e.title || `Event ${e.event_id}`,
          chapter: e.chapter_number,
          typeBadge: e.event_type,
        }));
    } else {
      const nodes = characterDiscoveryQuery.data?.nodes || [];
      return nodes.map((n) => ({
        id: n.id,
        label: n.label,
        chapter: n.chapter,
        typeBadge: n.node_type,
      }));
    }
  }, [mode, timelineDiscoveryQuery.data?.events, characterDiscoveryQuery.data?.nodes, readerChapter]);

  // Clean derivation of activeTargetId (Temporal Hardening: invalid if not in current discoveryItems)
  const activeTargetItem = useMemo(() => {
    if (!selectedTargetId) return null;
    return discoveryItems.find((it) => it.id === selectedTargetId) || null;
  }, [selectedTargetId, discoveryItems]);

  const activeTargetId = activeTargetItem ? activeTargetItem.id : null;

  // Filter discovery items locally
  const filteredDiscoveryItems = useMemo(() => {
    if (!searchQuery.trim()) return discoveryItems;
    const q = searchQuery.toLowerCase().trim();
    return discoveryItems.filter(
      (it) => it.label.toLowerCase().includes(q) || it.id.toLowerCase().includes(q)
    );
  }, [discoveryItems, searchQuery]);

  // 2. Overview Topology Query (When no specific target is selected)
  const causalTopologyQuery = useStoryGraph(
    activeSeriesId,
    readerChapter,
    'causal',
    !activeTargetId
  );

  // 3. Deep Investigation Queries (Dispatched ONLY on-demand for active target: Zero N+1)
  const eventCausalityQuery = useEventNarrativeExplanation(
    activeSeriesId,
    activeTargetId || '',
    readerChapter,
    4,
    mode === 'EVENT' && !!activeTargetId
  );

  const characterCausalityQuery = useCharacterNarrativeCausality(
    activeSeriesId,
    activeTargetId || '',
    readerChapter,
    4,
    mode === 'CHARACTER' && !!activeTargetId
  );

  const activeDeepQuery = mode === 'EVENT' ? eventCausalityQuery : characterCausalityQuery;
  const activeDeepData = activeDeepQuery.data;

  // Determine active flow nodes & edges using strict separate adapters (RULE_03)
  const { flowNodes, flowEdges } = useMemo(() => {
    if (!activeTargetId) {
      // Full causal topology overview
      const nodes = causalTopologyQuery.data?.nodes || [];
      const edges = causalTopologyQuery.data?.edges || [];
      return adaptCausalGraph(nodes, edges, null);
    } else {
      // Deep causal narrative path/steps for target
      const steps = activeDeepData?.narrative_steps || [];
      return adaptNarrativeCausalSteps(steps, selectedStepId);
    }
  }, [activeTargetId, causalTopologyQuery.data, activeDeepData?.narrative_steps, selectedStepId]);

  const activeSelectedStep = useMemo(() => {
    if (!selectedStepId || !activeDeepData?.narrative_steps) return null;
    return activeDeepData.narrative_steps.find((s) => s.step_id === selectedStepId) || null;
  }, [selectedStepId, activeDeepData?.narrative_steps]);

  // Node click handler inside graph viewport
  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node: Node) => {
      if (!selectedTargetId) {
        // In overview topology: clicking an event node selects it as the active investigation target!
        handleSelectTarget(node.id);
      } else {
        // In target view: find matching step
        const matchingStep = activeDeepData?.narrative_steps?.find(
          (s) => s.source_event_id === node.id || s.target_event_id === node.id
        );
        if (matchingStep) {
          setSelectedStepId((prev) => (prev === matchingStep.step_id ? null : matchingStep.step_id));
        }
      }
    },
    [selectedTargetId, handleSelectTarget, activeDeepData?.narrative_steps]
  );

  // Inspector integration: houses full detailed synthesis, conflicts, and state JSON (RULE_05)
  const handleOpenInspector = useCallback(() => {
    if (!selectedTargetId) return;

    const title = activeTargetItem ? activeTargetItem.label : selectedTargetId;
    const headline = activeDeepData?.headline;
    const conflicts = activeDeepData?.conflicts || [];
    const impactBreakdown = activeDeepData?.impact_breakdown || {};
    const steps = activeDeepData?.narrative_steps || [];

    openInspector({
      title: `${mode}: ${title}`,
      subtitle: `Causal Horizon: Chapter ${readerChapter}`,
      badge: {
        label: 'CAUSAL SYNTHESIS',
        variant: 'temporal',
      },
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.875rem' }}>
          {headline && (
            <div>
              <div
                style={{
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  color: 'var(--tsi-text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '4px',
                }}
              >
                Synthesized Narrative Headline
              </div>
              <p style={{ margin: 0, color: 'var(--tsi-text-primary)', fontStyle: 'italic' }}>
                "{headline}"
              </p>
            </div>
          )}

          {/* Impact Distribution Breakdown */}
          {Object.keys(impactBreakdown).length > 0 && (
            <div>
              <div
                style={{
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  color: 'var(--tsi-text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '6px',
                }}
              >
                Impact Dimension Distribution
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {Object.entries(impactBreakdown).map(([dim, count]) => (
                  <Badge key={dim} variant="neutral">
                    {dim}: {count}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Causal Steps List */}
          <div>
            <div
              style={{
                fontSize: '0.6875rem',
                fontWeight: 600,
                color: 'var(--tsi-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: '6px',
              }}
            >
              Causal Steps ({steps.length})
            </div>
            {steps.length === 0 ? (
              <div style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-muted)', fontStyle: 'italic' }}>
                No causal steps recorded at or before Chapter {readerChapter}.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '200px', overflowY: 'auto' }}>
                {steps.map((step) => (
                  <div
                    key={step.step_id}
                    style={{
                      padding: '8px 10px',
                      backgroundColor: 'var(--tsi-surface-secondary)',
                      borderRadius: 'var(--tsi-radius-sm)',
                      fontSize: '0.8125rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '3px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
                        {step.relation_type}
                      </span>
                      <Badge variant="neutral">{step.confidence}</Badge>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--tsi-text-secondary)' }}>
                      {step.state_change_summary}
                    </div>
                    {step.evidence_rule_id && (
                      <div style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', fontFamily: 'var(--tsi-font-mono)' }}>
                        Rule: {step.evidence_rule_id} • {step.explanation_code}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Narrative Conflicts */}
          {conflicts.length > 0 && (
            <div>
              <div
                style={{
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  color: 'var(--tsi-status-warning)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '6px',
                }}
              >
                Causal Conflicts ({conflicts.length})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {conflicts.map((c) => (
                  <div
                    key={c.conflict_id}
                    style={{
                      padding: '8px 10px',
                      backgroundColor: 'var(--tsi-surface-secondary)',
                      borderRadius: 'var(--tsi-radius-sm)',
                      fontSize: '0.8125rem',
                      color: 'var(--tsi-text-secondary)',
                    }}
                  >
                    <strong>{c.conflict_type}:</strong> {c.evidence_summary}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ),
    });
  }, [
    selectedTargetId,
    activeTargetItem,
    activeDeepData,
    mode,
    readerChapter,
    openInspector,
  ]);

  const isLoading = selectedTargetId
    ? activeDeepQuery.isLoading
    : causalTopologyQuery.isLoading;

  const isError = selectedTargetId
    ? activeDeepQuery.isError
    : causalTopologyQuery.isError;

  const error = selectedTargetId ? activeDeepQuery.error : causalTopologyQuery.error;

  return (
    <div
      data-testid="causal-investigation-page"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        minHeight: 'calc(100vh - 120px)',
      }}
    >
      {/* Header */}
      <CausalityHeader
        seriesId={activeSeriesId}
        readerChapter={readerChapter}
        totalChapters={totalChapters}
        activeMode={mode}
        targetTitle={activeTargetItem?.label}
        nodeCount={flowNodes.length}
        edgeCount={flowEdges.length}
        onJumpToStart={handleJumpToStart}
        onJumpToHorizon={handleJumpToHorizon}
        onStepBackward={canStepBackward ? handleStepBackward : undefined}
        onStepForward={canStepForward ? handleStepForward : undefined}
        canStepBackward={canStepBackward}
        canStepForward={canStepForward}
      />

      {/* Investigation Controls: Target Selection & Discovery */}
      <CausalInvestigationControls
        mode={mode}
        onModeChange={handleModeChange}
        items={filteredDiscoveryItems}
        selectedId={selectedTargetId}
        onSelectId={handleSelectTarget}
        searchQuery={searchQuery}
        onSearchQueryChange={setSearchQuery}
        isLoadingDiscovery={
          mode === 'EVENT'
            ? timelineDiscoveryQuery.isLoading
            : characterDiscoveryQuery.isLoading
        }
      />

      {/* Main Workspace Area */}
      {isLoading ? (
        <div data-testid="causality-loading-state" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Skeleton height="560px" borderRadius="var(--tsi-radius-lg)" />
        </div>
      ) : isError ? (
        <div data-testid="causality-error-state" style={{ padding: '24px 0' }}>
          <ErrorState
            title="Failed to Load Causal Intelligence"
            message={
              error instanceof Error
                ? error.message
                : 'An unexpected error occurred while retrieving causal models.'
            }
            onRetry={() => {
              if (selectedTargetId) {
                activeDeepQuery.refetch();
              } else {
                causalTopologyQuery.refetch();
              }
            }}
          />
        </div>
      ) : flowNodes.length === 0 ? (
        <div data-testid="causality-empty-state" style={{ padding: '32px 0' }}>
          <EmptyState
            title="No Causal Connections Established"
            description={`No causal relations or downstream effects have been established at or before Chapter ${readerChapter}. Advance the reader horizon to observe emerging causal chains.`}
            actionLabel={canStepForward ? 'Advance to Next Chapter' : undefined}
            onAction={canStepForward ? handleStepForward : undefined}
          />
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1fr) 340px',
            gap: '16px',
            alignItems: 'start',
          }}
        >
          {/* React Flow Causal Viewport */}
          <div
            data-testid="causal-viewport-container"
            style={{
              height: '620px',
              backgroundColor: 'var(--tsi-surface-primary)',
              border: '1px solid var(--tsi-border-subtle)',
              borderRadius: 'var(--tsi-radius-lg)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <ReactFlow
              nodes={flowNodes}
              edges={flowEdges}
              nodeTypes={nodeTypes}
              onNodeClick={onNodeClick}
              fitView
              minZoom={0.2}
              maxZoom={2.5}
              proOptions={{ hideAttribution: true }}
            >
              <Background
                variant={BackgroundVariant.Dots}
                gap={24}
                size={1.5}
                color="rgba(148, 163, 184, 0.15)"
              />
              <Controls position="bottom-right" showInteractive={false} />
              <MiniMap
                position="bottom-left"
                nodeColor={() => 'var(--tsi-accent-primary)'}
                maskColor="rgba(15, 23, 42, 0.75)"
                style={{
                  backgroundColor: 'var(--tsi-surface-elevated)',
                  border: '1px solid var(--tsi-border-subtle)',
                  borderRadius: 'var(--tsi-radius-md)',
                  width: 140,
                  height: 90,
                }}
              />
            </ReactFlow>

            {/* Semantic Legend Overlay */}
            <div
              style={{
                position: 'absolute',
                bottom: '12px',
                left: '160px',
                zIndex: 4,
              }}
            >
              <CausalLegend />
            </div>

            {/* Target Status Banner */}
            <div
              style={{
                position: 'absolute',
                top: '12px',
                left: '12px',
                zIndex: 4,
                backgroundColor: 'var(--tsi-surface-elevated)',
                border: '1px solid var(--tsi-border-default)',
                borderRadius: 'var(--tsi-radius-sm)',
                padding: '5px 12px',
                fontSize: '0.75rem',
                color: 'var(--tsi-text-secondary)',
              }}
            >
              {activeTargetId ? (
                <span>
                  Focus: <strong style={{ color: 'var(--tsi-accent-primary)' }}>{activeTargetItem?.label || activeTargetId}</strong> ({flowNodes.length} nodes)
                </span>
              ) : (
                <span>Overview Topology ({flowNodes.length} events)</span>
              )}
            </div>
          </div>

          {/* Contextual Side Panel: Compact Summary */}
          <div style={{ position: 'sticky', top: '16px' }}>
            <CausalSelectionSummary
              seriesId={activeSeriesId}
              readerChapter={readerChapter}
              mode={mode}
              targetId={activeTargetId}
              targetTitle={activeTargetItem?.label}
              synthesis={activeDeepData}
              selectedStep={activeSelectedStep}
              onOpenInspector={handleOpenInspector}
              onClearTarget={() => handleSelectTarget('')}
            />
          </div>
        </div>
      )}
    </div>
  );
};
