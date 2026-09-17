import React, { useMemo, useState, useEffect } from 'react';
import { ReactFlow, Controls, Background, useNodesState, useEdgesState } from '@xyflow/react';
import { useReader } from '../../reader/reader-store';
import { useCharacterGraph } from '../hooks/useCharacterGraph';
import { transformDomainGraphToReactFlow } from '../utils/graph-adapter';
import { CharacterNodeComponent } from './RelationshipNode';
import { GraphToolbar } from './GraphToolbar';
import { RelationshipDetails } from './RelationshipDetails';

const nodeTypes = {
  character: CharacterNodeComponent,
};

export const CharacterGraph: React.FC<{ seriesId: string, characterId: string }> = ({ seriesId, characterId }) => {
  const { readerChapter } = useReader();
  const [depth, setDepth] = useState<number>(1);
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  
  // Edge selection state
  const [selectedEdge, setSelectedEdge] = useState<{ sourceId: string, targetId: string, sourceName: string, targetName: string } | null>(null);

  const { data: domainGraph, isLoading, isError } = useCharacterGraph(seriesId, characterId, readerChapter, depth);

  const { initialNodes, initialEdges } = useMemo(() => {
    if (!domainGraph) return { initialNodes: [], initialEdges: [] };
    
    // Filter edges by typeFilter on the client side as requested (API returns all active up to depth)
    const filteredEdges = typeFilter === 'ALL' 
      ? domainGraph.edges 
      : domainGraph.edges.filter(e => e.type === typeFilter);
      
    // Reconstruct nodes that belong to the filtered edges, plus the root node
    const connectedNodeIds = new Set<string>([domainGraph.root_character_id]);
    filteredEdges.forEach(e => {
      connectedNodeIds.add(e.source);
      connectedNodeIds.add(e.target);
    });
    const filteredNodes = domainGraph.nodes.filter(n => connectedNodeIds.has(n.id));
    
    const transformed = transformDomainGraphToReactFlow({
      nodes: filteredNodes,
      edges: filteredEdges
    });
    
    // Visually distinguish the root node
    transformed.nodes = transformed.nodes.map(n => {
      if (n.id === domainGraph.root_character_id) {
        return {
          ...n,
          style: { ...n.style, border: '3px solid #f1c40f', boxShadow: '0 0 15px rgba(241, 196, 15, 0.5)', transform: 'scale(1.1)' }
        };
      }
      return n;
    });
    
    return { initialNodes: transformed.nodes, initialEdges: transformed.edges };
  }, [domainGraph, typeFilter]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync state when data changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    // Clear selection on data change to prevent stale data
    setSelectedEdge(null);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onEdgeClick = (event: React.MouseEvent, edge: any) => {
    const sourceNode = nodes.find(n => n.id === edge.source);
    const targetNode = nodes.find(n => n.id === edge.target);
    if (sourceNode && targetNode) {
      setSelectedEdge({
        sourceId: edge.source,
        targetId: edge.target,
        sourceName: sourceNode.data.name as string,
        targetName: targetNode.data.name as string
      });
    }
  };

  const rootNode = domainGraph?.nodes.find(n => n.id === domainGraph.root_character_id);

  if (isError) return <p style={{ color: '#e74c3c' }}>Character has not been introduced by this chapter.</p>;
  if (isLoading) return <p>Loading character graph...</p>;
  if (!domainGraph) return null;

  return (
    <div style={{ height: '500px', border: '1px solid #ccc', borderRadius: '8px', position: 'relative', marginTop: '24px' }}>
      <GraphToolbar 
        depth={depth} 
        onDepthChange={setDepth} 
        typeFilter={typeFilter} 
        onTypeFilterChange={setTypeFilter} 
        rootName={rootNode?.name || 'Unknown'} 
      />
      
      {selectedEdge && (
        <RelationshipDetails 
          seriesId={seriesId} 
          sourceId={selectedEdge.sourceId} 
          targetId={selectedEdge.targetId} 
          sourceName={selectedEdge.sourceName}
          targetName={selectedEdge.targetName}
          onClose={() => setSelectedEdge(null)} 
        />
      )}
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onEdgeClick={onEdgeClick}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
};
