import React from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { UniversalGraphNode, UniversalGraphEdge } from '../../../api/contracts/read-models';

export interface GraphSelectionSummaryProps {
  seriesId: string;
  readerChapter: number;
  selectedNode: UniversalGraphNode | null;
  allNodes: UniversalGraphNode[];
  edges: UniversalGraphEdge[];
  onInspect: (character: UniversalGraphNode) => void;
  onClearSelection: () => void;
}

export const GraphSelectionSummary: React.FC<GraphSelectionSummaryProps> = ({
  seriesId,
  readerChapter,
  selectedNode,
  allNodes,
  edges,
  onInspect,
  onClearSelection,
}) => {
  if (!selectedNode) {
    return (
      <div
        data-testid="graph-selection-empty"
        style={{
          padding: '16px',
          backgroundColor: 'var(--tsi-surface-primary)',
          border: '1px dashed var(--tsi-border-subtle)',
          borderRadius: 'var(--tsi-radius-md)',
          color: 'var(--tsi-text-muted)',
          fontSize: '0.8125rem',
          textAlign: 'center',
        }}
      >
        Select a character node in the graph to inspect relationship connections.
      </div>
    );
  }

  // Find incoming and outgoing edges for this character
  const connectedEdges = edges.filter(
    (e) => e.source_id === selectedNode.id || e.target_id === selectedNode.id
  );

  const nodeMap = new Map<string, UniversalGraphNode>();
  allNodes.forEach((n) => nodeMap.set(n.id, n));

  return (
    <div
      data-testid="graph-selection-summary"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        padding: '16px',
        backgroundColor: 'var(--tsi-surface-primary)',
        border: '1px solid var(--tsi-border-subtle)',
        borderRadius: 'var(--tsi-radius-md)',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.25)',
      }}
    >
      {/* Header with character name and close button */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <h3
              data-testid="selected-character-name"
              style={{
                margin: 0,
                fontSize: '1.0625rem',
                fontWeight: 600,
                color: 'var(--tsi-text-primary)',
              }}
            >
              {selectedNode.label}
            </h3>
            <Badge variant="default">{selectedNode.node_type}</Badge>
          </div>
          <div
            style={{
              fontSize: '0.6875rem',
              color: 'var(--tsi-text-muted)',
              fontFamily: 'var(--tsi-font-mono)',
              marginTop: '2px',
            }}
          >
            ID: {selectedNode.id}
          </div>
        </div>

        <button
          type="button"
          onClick={onClearSelection}
          aria-label="Clear character selection"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--tsi-text-muted)',
            cursor: 'pointer',
            fontSize: '1.25rem',
            lineHeight: 1,
            padding: '2px 6px',
            borderRadius: 'var(--tsi-radius-sm)',
          }}
        >
          ×
        </button>
      </div>

      {/* Quick Actions */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onInspect(selectedNode)}
          aria-label="Open character in inspector drawer"
          data-testid="inspect-character-btn"
        >
          Open Inspector
        </Button>

        <Link
          to={`/series/${seriesId}/characters/${selectedNode.id}?chapter=${readerChapter}`}
          style={{ textDecoration: 'none' }}
        >
          <Button size="sm" variant="primary" data-testid="view-profile-link">
            Full Profile →
          </Button>
        </Link>
      </div>

      {/* Relationships connection list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
        <div
          style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: 'var(--tsi-text-muted)',
          }}
        >
          Connections ({connectedEdges.length})
        </div>

        {connectedEdges.length === 0 ? (
          <div
            style={{
              fontSize: '0.75rem',
              color: 'var(--tsi-text-muted)',
              fontStyle: 'italic',
              padding: '6px 0',
            }}
          >
            No active relationships recorded at or before Chapter {readerChapter}.
          </div>
        ) : (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              maxHeight: '220px',
              overflowY: 'auto',
            }}
          >
            {connectedEdges.map((edge) => {
              const isOutgoing = edge.source_id === selectedNode.id;
              const targetNodeId = isOutgoing ? edge.target_id : edge.source_id;
              const counterpart = nodeMap.get(targetNodeId);
              const counterpartName = counterpart ? counterpart.label : targetNodeId;

              return (
                <div
                  key={edge.edge_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '8px',
                    padding: '6px 10px',
                    backgroundColor: 'var(--tsi-surface-secondary)',
                    borderRadius: 'var(--tsi-radius-sm)',
                    border: '1px solid var(--tsi-border-subtle)',
                    fontSize: '0.8125rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        color: isOutgoing ? 'var(--tsi-accent-primary)' : 'var(--tsi-status-warning)',
                      }}
                      title={isOutgoing ? 'Outgoing connection' : 'Incoming connection'}
                    >
                      {isOutgoing ? '→' : '←'}
                    </span>
                    <span
                      data-testid="connection-counterpart-name"
                      style={{
                        fontWeight: 500,
                        color: 'var(--tsi-text-primary)',
                      }}
                    >
                      {counterpartName}
                    </span>
                  </div>

                  <Badge variant="neutral">
                    {edge.label || edge.edge_type}
                  </Badge>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
