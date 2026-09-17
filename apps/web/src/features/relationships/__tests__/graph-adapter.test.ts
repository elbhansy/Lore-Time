import { describe, it, expect } from 'vitest';
import { transformDomainGraphToReactFlow } from '../utils/graph-adapter';
import { RelationshipGraphResponse } from '../../../types/api';

const mockGraph: RelationshipGraphResponse = {
  nodes: [
    { id: 'A', name: 'Char A', rank: 'A', alive: true },
    { id: 'B', name: 'Char B', rank: 'B', alive: true }
  ],
  edges: [
    { id: 'A-B', source: 'A', target: 'B', type: 'ALLY', active: true }
  ]
};

describe('graph-adapter', () => {
  it('transforms domain graph to react flow formats', () => {
    const { nodes, edges } = transformDomainGraphToReactFlow(mockGraph);
    
    expect(nodes).toHaveLength(2);
    expect(nodes[0].id).toBe('A');
    expect(nodes[0].data.name).toBe('Char A');
    
    expect(edges).toHaveLength(1);
    expect(edges[0].id).toBe('A-B');
    expect(edges[0].label).toBe('ALLY');
    // ALLY should not be animated
    expect(edges[0].animated).toBe(false);
  });

  it('animates enemy relationships', () => {
    const enemyGraph: RelationshipGraphResponse = {
      nodes: [],
      edges: [{ id: 'A-B', source: 'A', target: 'B', type: 'ENEMY', active: true }]
    };
    
    const { edges } = transformDomainGraphToReactFlow(enemyGraph);
    expect(edges[0].animated).toBe(true);
  });
});
