import React, { useMemo } from 'react';
import { ReactFlow, Controls, Background, useNodesState, useEdgesState, Panel, Node } from '@xyflow/react';
import { useNavigate } from 'react-router-dom';
import '@xyflow/react/dist/style.css';
import { useReader } from '../../reader/reader-store';
import { useRelationshipGraph } from '../hooks/useRelationshipGraph';
import { transformDomainGraphToReactFlow } from '../utils/graph-adapter';
import { CharacterNodeComponent } from './RelationshipNode';

const nodeTypes = {
  character: CharacterNodeComponent,
};

export const RelationshipGraph: React.FC = () => {
  const { seriesId, readerChapter } = useReader();
  const [filterType, setFilterType] = React.useState('ALL');
  const navigate = useNavigate();
  
  const { data: domainGraph, isLoading } = useRelationshipGraph(seriesId, readerChapter, filterType);

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!domainGraph) return { nodes: [], edges: [] };
    return transformDomainGraphToReactFlow(domainGraph);
  }, [domainGraph]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  React.useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = React.useCallback((_: React.MouseEvent, node: Node) => {
    // Navigate to character profile, preserving URL state implicitly if it's based on query params 
    // or by letting reader-store manage it. Since readerChapter is in the URL, we pass it.
    navigate(`/series/${seriesId}/characters/${node.id}?chapter=${readerChapter}`);
  }, [navigate, seriesId, readerChapter]);

  if (isLoading) return <p>Loading relationship graph...</p>;
  if (!domainGraph || domainGraph.nodes.length === 0) return <p style={{ fontStyle: 'italic', color: '#7f8c8d' }}>No relationships discovered yet.</p>;

  const types = ['ALL', 'ALLY', 'ENEMY', 'FRIEND', 'RIVAL', 'FAMILY', 'MASTER', 'DISCIPLE'];

  return (
    <div style={{ height: '600px', border: '1px solid #ccc', borderRadius: '8px', marginTop: '32px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
        <Panel position="top-left" style={{ backgroundColor: 'rgba(255,255,255,0.9)', padding: '8px', borderRadius: '4px' }}>
          <h4>Filters</h4>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            {types.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </Panel>
      </ReactFlow>
    </div>
  );
};
