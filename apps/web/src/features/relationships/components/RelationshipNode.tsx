import React from 'react';
import { Handle, Position } from '@xyflow/react';

export const CharacterNodeComponent: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div style={{
      padding: '10px 20px',
      border: `2px solid ${data.alive ? '#3498db' : '#e74c3c'}`,
      borderRadius: '8px',
      backgroundColor: 'white',
      minWidth: '120px',
      textAlign: 'center',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
    }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontWeight: 'bold' }}>{data.name}</div>
      <div style={{ fontSize: '0.8em', color: '#7f8c8d' }}>Rank: {data.rank || 'None'}</div>
      {!data.alive && <div style={{ fontSize: '0.7em', color: '#e74c3c', fontWeight: 'bold' }}>DEAD</div>}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};
