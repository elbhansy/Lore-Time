import { RelationshipGraphResponse, CharacterNode, RelationshipEdge } from '../../../types/api';
import { Node, Edge, MarkerType } from '@xyflow/react';

const getEdgeStyle = (type: string) => {
  switch (type) {
    case 'ALLY':
    case 'FRIEND':
      return { stroke: '#27ae60', strokeWidth: 2 };
    case 'ENEMY':
    case 'RIVAL':
      return { stroke: '#c0392b', strokeWidth: 2, strokeDasharray: '5,5' };
    case 'FAMILY':
      return { stroke: '#8e44ad', strokeWidth: 3 };
    case 'MASTER':
    case 'DISCIPLE':
      return { stroke: '#f39c12', strokeWidth: 2 };
    default:
      return { stroke: '#7f8c8d', strokeWidth: 1 };
  }
};

const getEdgeMarker = (type: string) => {
  return {
    type: MarkerType.ArrowClosed,
    color: getEdgeStyle(type).stroke,
  };
};

export const transformDomainGraphToReactFlow = (domainGraph: RelationshipGraphResponse): { nodes: Node[], edges: Edge[] } => {
  // Very basic layout: Place nodes in a circle or grid
  const nodes: Node[] = domainGraph.nodes.map((n, i) => {
    // Simple circular layout for initial placement
    const radius = 200;
    const angle = (i / domainGraph.nodes.length) * 2 * Math.PI;
    const x = 300 + radius * Math.cos(angle);
    const y = 300 + radius * Math.sin(angle);
    
    return {
      id: n.id,
      type: 'character', // maps to custom node
      position: { x, y },
      data: { name: n.name, rank: n.rank, alive: n.alive }
    };
  });

  const edges: Edge[] = domainGraph.edges.map(e => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.type,
    animated: e.type === 'ENEMY' || e.type === 'RIVAL', // Example of dynamic styling
    style: getEdgeStyle(e.type),
    markerEnd: getEdgeMarker(e.type)
  }));

  return { nodes, edges };
};
