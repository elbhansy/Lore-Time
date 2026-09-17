import React, { useMemo, useState } from 'react';
import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useTemporalGraph } from '../hooks/useTemporalGraph';
import { adaptToReactFlow } from '../utils/graph-adapter';
import { useReader } from '../../reader/reader-store';
import { useNavigate } from 'react-router-dom';

export const KnowledgeGraph: React.FC = () => {
  const { seriesId, readerChapter } = useReader();
  const navigate = useNavigate();
  const { data: graphData, isLoading, isError } = useTemporalGraph(seriesId, readerChapter);

  // Simple UI-side filtering
  const [showFactions, setShowFactions] = useState(true);
  const [showSkills, setShowSkills] = useState(true);
  const [showPower, setShowPower] = useState(true);

  const { nodes, edges } = useMemo(() => {
    if (!graphData) return { nodes: [], edges: [] };
    
    // Filter nodes based on UI state
    const filteredNodes = graphData.nodes.filter(n => {
      if (!showFactions && n.type === 'FACTION') return false;
      if (!showSkills && n.type === 'SKILL') return false;
      if (!showPower && (n.type === 'POWER_SYSTEM' || n.type === 'RANK')) return false;
      return true;
    });
    
    const validNodeIds = new Set(filteredNodes.map(n => n.id));
    
    // Filter edges to only those where both source and target exist
    const filteredEdges = graphData.edges.filter(e => validNodeIds.has(e.source_id) && validNodeIds.has(e.target_id));
    
    return adaptToReactFlow({ reader_chapter: graphData.reader_chapter, nodes: filteredNodes, edges: filteredEdges });
  }, [graphData, showFactions, showSkills, showPower]);

  const onNodeClick = (event: React.MouseEvent, node: any) => {
    if (node.data.type === 'CHARACTER') {
      navigate(`/series/${seriesId}/characters/${node.id}?chapter=${readerChapter}`);
    }
  };

  if (isLoading) return <p>Loading Temporal Knowledge Graph...</p>;
  if (isError) return <p style={{ color: 'red' }}>Failed to load Knowledge Graph.</p>;

  return (
    <div style={{ height: '600px', border: '1px solid #ccc', borderRadius: '8px', position: 'relative' }}>
      <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 10, display: 'flex', gap: '8px', backgroundColor: 'rgba(255,255,255,0.9)', padding: '8px', borderRadius: '4px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '14px', cursor: 'pointer' }}>
          <input type="checkbox" checked={showFactions} onChange={(e) => setShowFactions(e.target.checked)} />
          Factions
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '14px', cursor: 'pointer' }}>
          <input type="checkbox" checked={showSkills} onChange={(e) => setShowSkills(e.target.checked)} />
          Skills
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '14px', cursor: 'pointer' }}>
          <input type="checkbox" checked={showPower} onChange={(e) => setShowPower(e.target.checked)} />
          Power & Ranks
        </label>
      </div>

      <ReactFlow 
        nodes={nodes} 
        edges={edges}
        onNodeClick={onNodeClick}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
};
