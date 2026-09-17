import { UniversalGraphNode, UniversalGraphEdge } from '../../../api/contracts/read-models';
import { Node, Edge, MarkerType } from '@xyflow/react';

export interface GraphColorConfig {
  stroke: string;
  strokeWidth: number;
  strokeDasharray?: string;
  animated?: boolean;
}

export const getRelationshipEdgeStyle = (edgeType: string): GraphColorConfig => {
  const norm = edgeType.toUpperCase();
  switch (norm) {
    case 'ALLY':
    case 'ALLIED':
    case 'FRIEND':
      return { stroke: '#10b981', strokeWidth: 2, animated: false };
    case 'ENEMY':
    case 'HOSTILE':
    case 'RIVAL':
      return { stroke: '#ef4444', strokeWidth: 2, strokeDasharray: '5,5', animated: true };
    case 'FAMILY':
    case 'KIN':
      return { stroke: '#8b5cf6', strokeWidth: 2.5, animated: false };
    case 'MASTER':
    case 'MENTOR':
    case 'DISCIPLE':
      return { stroke: '#f59e0b', strokeWidth: 2, animated: false };
    case 'SUBORDINATE':
    case 'COMMANDER':
      return { stroke: '#38bdf8', strokeWidth: 2, animated: false };
    default:
      return { stroke: '#64748b', strokeWidth: 1.5, animated: false };
  }
};

export const transformUniversalGraphToReactFlow = (
  nodes: UniversalGraphNode[],
  edges: UniversalGraphEdge[],
  selectedNodeId: string | null = null
): { flowNodes: Node[]; flowEdges: Edge[] } => {
  const count = nodes.length;
  const radius = Math.max(180, Math.min(420, count * 35));
  const centerX = 400;
  const centerY = 320;

  const flowNodes: Node[] = nodes.map((node, index) => {
    const angle = count > 0 ? (index / count) * 2 * Math.PI : 0;
    const x = count === 1 ? centerX : centerX + radius * Math.cos(angle);
    const y = count === 1 ? centerY : centerY + radius * Math.sin(angle);
    const isSelected = selectedNodeId === node.id;

    return {
      id: node.id,
      type: 'characterNode',
      position: { x, y },
      data: {
        id: node.id,
        label: node.label,
        nodeType: node.node_type,
        chapter: node.chapter,
        metadata: node.metadata,
        isSelected,
      },
    };
  });

  const flowEdges: Edge[] = edges.map((edge) => {
    const edgeConfig = getRelationshipEdgeStyle(edge.label || edge.edge_type);
    const isConnectedToSelected =
      selectedNodeId !== null && (edge.source_id === selectedNodeId || edge.target_id === selectedNodeId);

    return {
      id: edge.edge_id,
      source: edge.source_id,
      target: edge.target_id,
      label: edge.label,
      animated: edgeConfig.animated,
      type: 'smoothstep',
      style: {
        stroke: isConnectedToSelected ? 'var(--tsi-accent-primary)' : edgeConfig.stroke,
        strokeWidth: isConnectedToSelected ? edgeConfig.strokeWidth + 1.5 : edgeConfig.strokeWidth,
        strokeDasharray: edgeConfig.strokeDasharray,
        opacity: selectedNodeId ? (isConnectedToSelected ? 1 : 0.25) : 0.85,
        transition: 'all 0.2s ease',
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isConnectedToSelected ? 'var(--tsi-accent-primary)' : edgeConfig.stroke,
        width: 14,
        height: 14,
      },
      labelStyle: {
        fill: isConnectedToSelected ? '#f1f5f9' : '#94a3b8',
        fontSize: '0.6875rem',
        fontWeight: isConnectedToSelected ? 600 : 500,
        fontFamily: 'var(--tsi-font-mono)',
      },
      labelBgStyle: {
        fill: '#161922',
        fillOpacity: 0.9,
      },
      labelBgPadding: [4, 2] as [number, number],
      labelBgBorderRadius: 4,
    };
  });

  return { flowNodes, flowEdges };
};
