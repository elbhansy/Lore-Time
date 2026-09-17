import React from 'react';
import { useReader } from '../../reader/reader-store';
import { usePowerSystems, useRanks } from '../hooks/usePowerSystems';
import { RankList } from './RankList';
import { PowerSystemStats } from '../../power-intelligence/components/PowerSystemStats';

const PowerSystemCard: React.FC<{ seriesId: string, systemId: string, name: string, description: string | null }> = ({ seriesId, systemId, name, description }) => {
  const { readerChapter } = useReader();
  const { data: ranks, isLoading } = useRanks(seriesId, systemId, readerChapter);

  return (
    <div style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '16px', minWidth: '300px', flex: 1 }}>
      <h4 style={{ margin: '0 0 8px 0' }}>{name}</h4>
      {description && <p style={{ fontSize: '0.9em', color: '#555' }}>{description}</p>}
      
      <h5 style={{ margin: '16px 0 8px 0' }}>Known Ranks</h5>
      {isLoading ? <p>Loading ranks...</p> : <RankList ranks={ranks || []} />}
      
      <PowerSystemStats powerSystemId={systemId} />
    </div>
  );
};

export const PowerSystemExplorer: React.FC = () => {
  const { seriesId } = useReader();
  const { data: systems, isLoading } = usePowerSystems(seriesId);

  if (isLoading) return <p>Loading power systems...</p>;
  if (!systems || systems.length === 0) return null;

  return (
    <div style={{ marginTop: '32px' }}>
      <h3>Power Systems</h3>
      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
        {systems.map(sys => (
          <PowerSystemCard 
            key={sys.id} 
            seriesId={seriesId} 
            systemId={sys.id} 
            name={sys.name} 
            description={sys.description} 
          />
        ))}
      </div>
    </div>
  );
};
