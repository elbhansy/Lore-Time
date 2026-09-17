import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useReader } from '../../reader/reader-store';
import { useFaction } from '../hooks/useFactions';
import { FactionMembers } from './FactionMembers';
import { FactionLeadership } from './FactionLeadership';
// import { FactionTimeline } from './FactionTimeline';
// import { FactionGraph } from './FactionGraph';

type TabType = 'overview' | 'members' | 'leadership' | 'timeline' | 'graph';

export const FactionProfile: React.FC = () => {
  const { factionId } = useParams<{ factionId: string }>();
  const { seriesId, readerChapter } = useReader();
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  const { data: profile, isLoading, isError } = useFaction(seriesId, factionId || '', readerChapter);

  if (isLoading) return <p>Loading faction profile...</p>;
  if (isError || !profile) return <p style={{ color: 'red' }}>Failed to load faction.</p>;

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ borderBottom: '2px solid #ecf0f1', paddingBottom: '24px', marginBottom: '24px' }}>
        <h1 style={{ margin: '0 0 8px 0', color: '#2c3e50' }}>{profile.name}</h1>
        {profile.description && <p style={{ color: '#7f8c8d', fontSize: '1.1em', marginTop: 0 }}>{profile.description}</p>}
        
        <div style={{ display: 'flex', gap: '24px', marginTop: '16px', color: '#34495e' }}>
          <div><strong>Introduced:</strong> Chapter {profile.introduced_chapter}</div>
          <div><strong>Active Members:</strong> {profile.member_count}</div>
          <div><strong>Current Leader:</strong> {profile.leader_name || 'None'}</div>
          <div><strong>Active Alliances/Enmities:</strong> {profile.active_relationships_count}</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #bdc3c7', paddingBottom: '8px', marginBottom: '24px' }}>
        {['overview', 'members', 'leadership', 'timeline', 'graph'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as TabType)}
            style={{
              padding: '8px 16px',
              backgroundColor: activeTab === tab ? '#3498db' : 'transparent',
              color: activeTab === tab ? 'white' : '#7f8c8d',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: activeTab === tab ? 'bold' : 'normal',
              textTransform: 'capitalize'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      <div>
        {activeTab === 'overview' && (
          <div>
            <h3>Faction Overview</h3>
            <p>Select a tab above to explore the temporal state of {profile.name} at Chapter {readerChapter}.</p>
          </div>
        )}
        {activeTab === 'members' && factionId && <FactionMembers factionId={factionId} />}
        {activeTab === 'leadership' && factionId && <FactionLeadership factionId={factionId} />}
        {/* Placeholder for timeline and graph which will be implemented next */}
        {activeTab === 'timeline' && <p>Timeline implementation pending...</p>}
        {activeTab === 'graph' && <p>Graph implementation pending...</p>}
      </div>
    </div>
  );
};
