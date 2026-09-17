import React from 'react';
import { useReader } from '../features/reader/reader-store';
import { ChapterSelector } from '../features/reader/components/ChapterSelector';
import { useWorldState } from '../features/world-state/queries';
import { useSearchParams } from 'react-router-dom';
import { Timeline } from '../features/timeline/components/Timeline';
import { PowerSystemExplorer } from '../features/power-system/components/PowerSystemExplorer';
import { KnowledgeGraph } from '../features/knowledge-graph/components/KnowledgeGraph';
import { FactionExplorer } from '../features/factions/components/FactionExplorer';
import { SkillExplorer } from '../features/skills/components/SkillExplorer';
import { CharacterExplorer } from '../features/characters/components/CharacterExplorer';
import { TemporalComparison } from '../features/comparison/components/TemporalComparison';
import { GlobalSearch } from '../features/search/components/GlobalSearch';
import { AnalyticsPage } from '../features/analytics/components/AnalyticsPage';

export const SeriesPage: React.FC = () => {
  const { seriesId, readerChapter } = useReader();
  const { data, isLoading, isError, error, refetch } = useWorldState(seriesId, readerChapter);

  type ViewState = 'power' | 'relationships' | 'characters' | 'factions' | 'skills' | 'timeline' | 'comparison';

  const TOTAL_CHAPTERS = 200;

  const [searchParams, setSearchParams] = useSearchParams();
  const currentView = searchParams.get('view') || 'overview';

  const setView = (view: string) => {
    setSearchParams((prev) => {
      prev.set('view', view);
      return prev;
    });
  };

  const tabStyle = (view: string) => ({
    padding: '8px 16px',
    cursor: 'pointer',
    borderBottom: currentView === view ? '3px solid #3498db' : '3px solid transparent',
    color: currentView === view ? '#3498db' : '#555',
    fontWeight: currentView === view ? 'bold' : 'normal',
    backgroundColor: 'transparent',
    borderTop: 'none', borderLeft: 'none', borderRight: 'none',
    outline: 'none'
  });

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Timeline Power Visualizer</h1>
        <GlobalSearch />
      </div>
      
      <div style={{ marginBottom: '32px', marginTop: '16px' }}>
        <ChapterSelector totalChapters={TOTAL_CHAPTERS} />
      </div>

      <div style={{ display: 'flex', borderBottom: '1px solid #ccc', marginBottom: '24px', gap: '8px' }}>
        <button style={tabStyle('overview')} onClick={() => setView('overview')}>Overview</button>
        <button style={tabStyle('timeline')} onClick={() => setView('timeline')}>Timeline</button>
        <button style={tabStyle('characters')} onClick={() => setView('characters')}>Characters</button>
        <button style={tabStyle('factions')} onClick={() => setView('factions')}>Factions</button>
        <button style={tabStyle('skills')} onClick={() => setView('skills')}>Skills</button>
        <button style={tabStyle('power')} onClick={() => setView('power')}>Power Systems</button>
        <button style={tabStyle('relationships')} onClick={() => setView('relationships')}>Relationships</button>
        <button style={tabStyle('comparison')} onClick={() => setView('comparison')}>Temporal Comparison</button>
        <button style={tabStyle('analytics')} onClick={() => setView('analytics')}>Analytics</button>
      </div>

      {currentView === 'overview' && (
        <div style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px' }}>
          <h3>World State @ Chapter {readerChapter}</h3>
          
          {isLoading && <p>Loading world state...</p>}
          
          {isError && (
            <div style={{ color: 'red' }}>
              <p>Unable to load world state: {error instanceof Error ? error.message : 'Unknown error'}</p>
              <button onClick={() => refetch()}>Retry</button>
            </div>
          )}
          
          {data && (
            <div>
              <p>Characters: {Object.keys(data.characters).length}</p>
              <p>Factions: {Object.keys(data.factions).length}</p>
              <p>Relationships: {data.relationships.length}</p>
              
              <details style={{ marginTop: '16px' }}>
                <summary>Raw JSON</summary>
                <pre style={{ background: '#f5f5f5', padding: '8px', overflowX: 'auto' }}>
                  {JSON.stringify(data, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      )}

      {currentView === 'power' && <PowerSystemExplorer />}
      {currentView === 'relationships' && <KnowledgeGraph />}
      {currentView === 'characters' && <CharacterExplorer />}
      {currentView === 'factions' && <FactionExplorer />}
      {currentView === 'skills' && <SkillExplorer />}
      {currentView === 'timeline' && <Timeline totalChapters={TOTAL_CHAPTERS} />}
      {currentView === 'comparison' && <TemporalComparison />}
      {currentView === 'analytics' && <AnalyticsPage />}
    </div>
  );
};
