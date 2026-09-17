import { UniversalGraphNode, UniversalGraphEdge, NarrativeCausalStepDTO } from '../../../api/contracts/read-models';
import { Node, Edge, MarkerType } from '@xyflow/react';

export interface CausalEdgeStyleConfig {
  stroke: string;
  strokeWidth: number;
  strokeDasharray?: string;
  animated?: boolean;
}

/**
 * Maps authoritative Phase 5.2 CausalRelationType to deterministic visual styling.
 * Closed enum:
 * DIRECT_CAUSE, INDIRECT_INFLUENCE, STATE_TRANSITION, RELATIONSHIP_CONSEQUENCE,
 * POWER_CONSEQUENCE, FACTION_CONSEQUENCE, CHARACTER_CONSEQUENCE, EVENT_CHAIN
 */
export const getCausalEdgeStyle = (relationType: string): CausalEdgeStyleConfig => {
  const norm = relationType.toUpperCase();
  switch (norm) {
    case 'DIRECT_CAUSE':
    case 'EVENT_CHAIN':
      return { stroke: '#38bdf8', strokeWidth: 2.5, animated: false };
    case 'INDIRECT_INFLUENCE':
      return { stroke: '#94a3b8', strokeWidth: 1.5, strokeDasharray: '5,5', animated: true };
    case 'STATE_TRANSITION':
      return { stroke: '#f59e0b', strokeWidth: 2, animated: false };
    case 'CHARACTER_CONSEQUENCE':
    case 'RELATIONSHIP_CONSEQUENCE':
      return { stroke: '#a855f7', strokeWidth: 2, animated: false };
    case 'POWER_CONSEQUENCE':
      return { stroke: '#ef4444', strokeWidth: 2, animated: false };
    case 'FACTION_CONSEQUENCE':
      return { stroke: '#10b981', strokeWidth: 2, animated: false };
    default:
      return { stroke: '#64748b', strokeWidth: 1.5, animated: false };
  }
};

/**
 * Adapter 1: Full causal topology mapping from GenericGraphReadModel (graph_type="causal").
 * Pure structural transformation with zero added intelligence.
 */
export const adaptCausalGraph = (
  nodes: UniversalGraphNode[],
  edges: UniversalGraphEdge[],
  selectedNodeId: string | null = null
): { flowNodes: Node[]; flowEdges: Edge[] } => {
  const count = nodes.length;
  const radius = Math.max(200, Math.min(460, count * 40));
  const centerX = 420;
  const centerY = 320;

  const flowNodes: Node[] = nodes.map((node, index) => {
    const angle = count > 0 ? (index / count) * 2 * Math.PI : 0;
    const x = count === 1 ? centerX : centerX + radius * Math.cos(angle);
    const y = count === 1 ? centerY : centerY + radius * Math.sin(angle);
    const isSelected = selectedNodeId === node.id;

    return {
      id: node.id,
      type: 'causalNode',
      position: { x, y },
      data: {
        id: node.id,
        label: node.label,
        nodeType: node.node_type || 'EVENT',
        chapter: node.chapter,
        metadata: node.metadata,
        isSelected,
      },
    };
  });

  const flowEdges: Edge[] = edges.map((edge) => {
    const edgeConfig = getCausalEdgeStyle(edge.label || edge.edge_type);
    const isConnectedToSelected =
      selectedNodeId !== null && (edge.source_id === selectedNodeId || edge.target_id === selectedNodeId);

    return {
      id: edge.edge_id,
      source: edge.source_id,
      target: edge.target_id,
      label: edge.label || edge.edge_type,
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

/**
 * Adapter 2: Linear narrative causal steps mapping from TemporalNarrativeCausalExplanationDTO.
 * Transforms sequential causal steps into clear horizontal flow layout.
 */
export const adaptNarrativeCausalSteps = (
  steps: NarrativeCausalStepDTO[],
  selectedStepId: string | null = null
): { flowNodes: Node[]; flowEdges: Edge[] } => {
  const flowNodes: Node[] = [];
  const flowEdges: Edge[] = [];
  const seenEventNodes = new Set<string>();

  let nodeIndex = 0;
  steps.forEach((step) => {
    // Ensure source node exists
    if (!seenEventNodes.has(step.source_event_id)) {
      seenEventNodes.add(step.source_event_id);
      flowNodes.push({
        id: step.source_event_id,
        type: 'causalNode',
        position: { x: 80 + nodeIndex * 240, y: 180 + (nodeIndex % 2) * 60 },
        data: {
          id: step.source_event_id,
          label: `Event ${step.source_event_id}`,
          nodeType: 'EVENT',
          chapter: step.chapter,
          isSelected: selectedStepId === step.step_id,
        },
      });
      nodeIndex++;
    }

    // Ensure target node exists
    if (!seenEventNodes.has(step.target_event_id)) {
      seenEventNodes.add(step.target_event_id);
      flowNodes.push({
        id: step.target_event_id,
        type: 'causalNode',
        position: { x: 80 + nodeIndex * 240, y: 180 + (nodeIndex % 2) * 60 },
        data: {
          id: step.target_event_id,
          label: `Event ${step.target_event_id}`,
          nodeType: 'EVENT',
          chapter: step.chapter,
          isSelected: selectedStepId === step.step_id,
        },
      });
      nodeIndex++;
    }

    const edgeConfig = getCausalEdgeStyle(step.relation_type);
    const isSelected = selectedStepId === step.step_id;

    flowEdges.push({
      id: step.step_id,
      source: step.source_event_id,
      target: step.target_event_id,
      label: `${step.relation_type} (${step.confidence})`,
      animated: edgeConfig.animated,
      type: 'smoothstep',
      style: {
        stroke: isSelected ? 'var(--tsi-accent-primary)' : edgeConfig.stroke,
        strokeWidth: isSelected ? edgeConfig.strokeWidth + 1.5 : edgeConfig.strokeWidth,
        strokeDasharray: edgeConfig.strokeDasharray,
        opacity: selectedStepId ? (isSelected ? 1 : 0.3) : 0.9,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isSelected ? 'var(--tsi-accent-primary)' : edgeConfig.stroke,
        width: 14,
        height: 14,
      },
      labelStyle: {
        fill: isSelected ? '#f1f5f9' : '#cbd5e1',
        fontSize: '0.6875rem',
        fontWeight: isSelected ? 600 : 500,
        fontFamily: 'var(--tsi-font-mono)',
      },
      labelBgStyle: {
        fill: '#161922',
        fillOpacity: 0.92,
      },
      labelBgPadding: [4, 2] as [number, number],
      labelBgBorderRadius: 4,
    });
  });

  return { flowNodes, flowEdges };
};
