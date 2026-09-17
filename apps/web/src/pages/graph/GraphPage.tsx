import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
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

import { useStoryGraph } from '../../features/temporal/queries/useIntelligenceQueries';
import { useTemporalContext } from '../../state/temporal/temporal-context';
import { useShellContext } from '../../state/shell/shell-context';
import { UniversalGraphNode } from '../../api/contracts/read-models';
import { GraphHeader } from '../../features/relationships/components/GraphHeader';
import { GraphCharacterNode } from '../../features/relationships/components/GraphCharacterNode';
import { GraphSelectionSummary } from '../../features/relationships/components/GraphSelectionSummary';
import { GraphLegend } from '../../features/relationships/components/GraphLegend';
import { transformUniversalGraphToReactFlow } from '../../features/relationships/utils/graphAdapter';
import { Skeleton } from '../../components/feedback/Skeleton';
import { ErrorState } from '../../components/feedback/ErrorState';
import { EmptyState } from '../../components/feedback/EmptyState';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';

const nodeTypes = {
  characterNode: GraphCharacterNode,
};

export const GraphPage: React.FC = () => {
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

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

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
      setSearchParams({ chapter: String(Math.max(1, readerChapter - 1)) }, { replace: true });
    }
  }, [canStepBackward, stepBackward, readerChapter, setSearchParams]);

  const handleStepForward = useCallback(() => {
    if (canStepForward) {
      stepForward();
      setSearchParams({ chapter: String(Math.min(totalChapters, readerChapter + 1)) }, { replace: true });
    }
  }, [canStepForward, stepForward, readerChapter, totalChapters, setSearchParams]);

  const handleJumpToStart = useCallback(() => {
    setReaderChapter(1);
    setSearchParams({ chapter: '1' }, { replace: true });
  }, [setReaderChapter, setSearchParams]);

  const handleJumpToHorizon = useCallback(() => {
    setReaderChapter(totalChapters);
    setSearchParams({ chapter: String(totalChapters) }, { replace: true });
  }, [setReaderChapter, totalChapters, setSearchParams]);

  // Query graph read model - strictly scoped to seriesId, readerChapter, and 'relationship' graph type
  // Note: this query returns GenericGraphReadModel, ensuring NO N+1 profile queries occur.
  const graphQuery = useStoryGraph(activeSeriesId, readerChapter, 'relationship');

  const isLoading = graphQuery.isLoading;
  const isError = graphQuery.isError;
  const error = graphQuery.error;
  const graphData = graphQuery.data;

  // Filter nodes locally if search query is entered (local defense-in-depth, strictly within already-loaded graph)
  const filteredNodes = useMemo(() => {
    const rawNodes = graphData?.nodes || [];
    if (!searchQuery.trim()) return rawNodes;
    const q = searchQuery.toLowerCase().trim();
    return rawNodes.filter(
      (n) => n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q)
    );
  }, [graphData?.nodes, searchQuery]);

  // Safely derive active selected node: if the selected node disappeared after a horizon change, activeSelectedNode is null
  const activeSelectedNodeId = useMemo(() => {
    if (!selectedNodeId) return null;
    const exists = (graphData?.nodes || []).some((n) => n.id === selectedNodeId);
    return exists ? selectedNodeId : null;
  }, [selectedNodeId, graphData?.nodes]);

  // Edges filtered to match visible nodes
  const filteredEdges = useMemo(() => {
    const rawEdges = graphData?.edges || [];
    if (!searchQuery.trim()) return rawEdges;
    const visibleIds = new Set(filteredNodes.map((n) => n.id));
    return rawEdges.filter((e) => visibleIds.has(e.source_id) && visibleIds.has(e.target_id));
  }, [graphData?.edges, filteredNodes, searchQuery]);

  // Transform to React Flow structure
  const { flowNodes, flowEdges } = useMemo(() => {
    return transformUniversalGraphToReactFlow(filteredNodes, filteredEdges, activeSelectedNodeId);
  }, [filteredNodes, filteredEdges, activeSelectedNodeId]);

  // Find currently selected node object from original contract nodes
  const selectedNode = useMemo(() => {
    if (!activeSelectedNodeId) return null;
    return (graphData?.nodes || []).find((n) => n.id === activeSelectedNodeId) || null;
  }, [activeSelectedNodeId, graphData?.nodes]);

  // Handler for node click in graph
  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node: Node) => {
      setSelectedNodeId((prev) => (prev === node.id ? null : node.id));
    },
    []
  );

  // Inspector integration via ShellContext
  const handleOpenInspector = useCallback(
    (character: UniversalGraphNode) => {
      const charEdges = (graphData?.edges || []).filter(
        (e) => e.source_id === character.id || e.target_id === character.id
      );

      openInspector({
        title: character.label,
        subtitle: `Character ID: ${character.id}`,
        badge: {
          label: character.node_type || 'CHARACTER',
          variant: 'temporal',
        },
        content: (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: 'var(--tsi-text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '4px',
                }}
              >
                Temporal Knowledge Horizon
              </div>
              <div style={{ fontSize: '0.875rem', color: 'var(--tsi-text-primary)' }}>
                Known Through Chapter {readerChapter}
              </div>
            </div>

            <div>
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: 'var(--tsi-text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '6px',
                }}
              >
                Active Relationships ({charEdges.length})
              </div>
              {charEdges.length === 0 ? (
                <div style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-muted)', fontStyle: 'italic' }}>
                  No relationships recorded at or before this chapter.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {charEdges.map((edge) => {
                    const isOutgoing = edge.source_id === character.id;
                    const otherId = isOutgoing ? edge.target_id : edge.source_id;
                    const otherNode = (graphData?.nodes || []).find((n) => n.id === otherId);
                    return (
                      <div
                        key={edge.edge_id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '6px 8px',
                          backgroundColor: 'var(--tsi-surface-secondary)',
                          borderRadius: 'var(--tsi-radius-sm)',
                          fontSize: '0.8125rem',
                        }}
                      >
                        <span style={{ color: 'var(--tsi-text-primary)' }}>
                          {isOutgoing ? '→ ' : '← '}
                          {otherNode ? otherNode.label : otherId}
                        </span>
                        <Badge variant="neutral">{edge.label || edge.edge_type}</Badge>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div style={{ marginTop: '8px' }}>
              <Link
                to={`/series/${activeSeriesId}/characters/${character.id}?chapter=${readerChapter}`}
                style={{ textDecoration: 'none' }}
              >
                <Button size="sm" variant="primary" style={{ width: '100%' }}>
                  View Full Narrative Profile →
                </Button>
              </Link>
            </div>
          </div>
        ),
      });
    },
    [graphData, openInspector, readerChapter, activeSeriesId]
  );

  return (
    <div
      data-testid="relationship-graph-page"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        minHeight: 'calc(100vh - 120px)',
      }}
    >
      {/* Header with Temporal Stepper & Metrics */}
      <GraphHeader
        seriesId={activeSeriesId}
        readerChapter={readerChapter}
        totalChapters={totalChapters}
        characterCount={graphData?.nodes?.length || 0}
        relationshipCount={graphData?.edges?.length || 0}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onStepBackward={canStepBackward ? handleStepBackward : undefined}
        onStepForward={canStepForward ? handleStepForward : undefined}
        onJumpToStart={handleJumpToStart}
        onJumpToHorizon={handleJumpToHorizon}
        canStepBackward={canStepBackward}
        canStepForward={canStepForward}
      />

      {/* Main Content Workspace */}
      {isLoading ? (
        <div data-testid="graph-loading-state" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Skeleton height="560px" borderRadius="var(--tsi-radius-lg)" />
        </div>
      ) : isError ? (
        <div data-testid="graph-error-state" style={{ padding: '24px 0' }}>
          <ErrorState
            title="Failed to Load Relationship Graph"
            message={
              error instanceof Error
                ? error.message
                : 'An unexpected network error occurred while retrieving graph intelligence.'
            }
            onRetry={() => graphQuery.refetch()}
          />
        </div>
      ) : !graphData || !graphData.nodes || graphData.nodes.length === 0 ? (
        <div data-testid="graph-empty-state" style={{ padding: '32px 0' }}>
          <EmptyState
            title="No Relationships Known"
            description={`No characters or relationships have been established at or before Chapter ${readerChapter}. Step forward in the temporal horizon to observe emerging connections.`}
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
          {/* React Flow Graph Viewport */}
          <div
            data-testid="graph-viewport-container"
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

            {/* Relationship Style Legend overlay */}
            <div
              style={{
                position: 'absolute',
                bottom: '12px',
                left: '160px',
                zIndex: 4,
              }}
            >
              <GraphLegend />
            </div>

            {/* Visual indicator for search match count */}
            {searchQuery && (
              <div
                style={{
                  position: 'absolute',
                  top: '12px',
                  left: '12px',
                  zIndex: 4,
                  backgroundColor: 'var(--tsi-surface-elevated)',
                  border: '1px solid var(--tsi-border-default)',
                  borderRadius: 'var(--tsi-radius-sm)',
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  color: 'var(--tsi-text-secondary)',
                }}
              >
                Showing {filteredNodes.length} of {graphData.nodes.length} characters
              </div>
            )}
          </div>

          {/* Contextual Side Panel for Selected Character */}
          <div style={{ position: 'sticky', top: '16px' }}>
            <GraphSelectionSummary
              seriesId={activeSeriesId}
              readerChapter={readerChapter}
              selectedNode={selectedNode}
              allNodes={graphData.nodes}
              edges={graphData.edges || []}
              onInspect={handleOpenInspector}
              onClearSelection={() => setSelectedNodeId(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
};
