import type { Node, Edge } from '@xyflow/react';
import { TemporalGraphDTO } from '../../../types/api';

const NODE_COLORS: Record<string, string> = {
  CHARACTER: '#3498db',
  FACTION: '#e67e22',
  POWER_SYSTEM: '#9b59b6',
  RANK: '#f1c40f',
  SKILL: '#2ecc71'
};

export const adaptToReactFlow = (graph: TemporalGraphDTO): { nodes: Node[], edges: Edge[] } => {
  const nodes: Node[] = graph.nodes.map((node, i) => {
    // Simple layout heuristic for prototype
    // In a real app we would use dagre or elK for layout
    const y = node.type === 'POWER_SYSTEM' ? 50 : node.type === 'RANK' ? 150 : node.type === 'FACTION' ? 100 : node.type === 'CHARACTER' ? 250 : 350;
    const x = 100 + (i * 120) % 800; // rough staggering
    
    return {
      id: node.id,
      position: { x, y },
      data: { 
        label: node.label,
        type: node.type,
      },
      style: {
        background: NODE_COLORS[node.type] || '#bdc3c7',
        color: node.type === 'RANK' ? '#333' : '#fff',
        border: '1px solid #333',
        borderRadius: node.type === 'FACTION' ? '4px' : '50px',
        padding: '10px',
        fontWeight: 'bold',
        fontSize: '12px',
        width: 120,
        textAlign: 'center'
      }
    };
  });

  const edges: Edge[] = graph.edges.map((edge, i) => ({
    id: `e-${edge.source_id}-${edge.target_id}-${edge.type}-${i}`,
    source: edge.source_id,
    target: edge.target_id,
    label: edge.type,
    type: 'smoothstep',
    animated: edge.type === 'MEMBER_OF' || edge.type === 'USES_POWER_SYSTEM',
    style: { stroke: '#7f8c8d', strokeWidth: 2 },
    labelStyle: { fill: '#7f8c8d', fontWeight: 'bold' },
    labelBgStyle: { fill: '#f8f9fa' }
  }));

  return { nodes, edges };
};
