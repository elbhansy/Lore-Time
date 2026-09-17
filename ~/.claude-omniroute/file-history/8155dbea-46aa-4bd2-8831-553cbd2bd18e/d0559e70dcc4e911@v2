import React from 'react';
import { useReader } from '../../reader/reader-store';
import {
  useAnalyticsOverview,
  useRelationshipStats,
} from '../hooks/useAnalytics';
import { OverviewPanel, EventDistribution } from './AnalyticsPanel';

const cardStyle: React.CSSProperties = {
  border: '1px solid #ccc',
  padding: '16px',
  borderRadius: '8px',
  marginBottom: '16px',
};

export const AnalyticsPage: React.FC = () => {
  const { seriesId } = useReader();
  const overview = useAnalyticsOverview(seriesId);
  const relationships = useRelationshipStats(seriesId);

  if (!seriesId) {
    return <p>Select a series to view analytics.</p>;
  }

  return (
    <div>
      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>Event Statistics</h3>
        {overview.isLoading && <p>Loading analytics…</p>}
        {overview.isError && (
          <div style={{ color: 'red' }}>
            <p>Unable to load analytics: {overview.error instanceof Error ? overview.error.message : 'Unknown error'}</p>
            <button onClick={() => overview.refetch()}>Retry</button>
          </div>
        )}
        {overview.data && (
          <>
            <OverviewPanel statistics={overview.data.statistics} />
            <EventDistribution
              title="Events by Type"
              buckets={overview.data.statistics.events_by_type}
              emptyMessage="No events published for this series yet."
            />
            <EventDistribution
              title="Events by Chapter"
              buckets={overview.data.statistics.events_by_chapter}
            />
            <EventDistribution
              title="Events by Sequence Position"
              buckets={overview.data.statistics.events_by_sequence}
            />
          </>
        )}
      </div>

      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>Relationship Statistics</h3>
        {relationships.isLoading && <p>Loading relationship analytics…</p>}
        {relationships.isError && (
          <p style={{ color: 'red' }}>
            Unable to load: {relationships.error instanceof Error ? relationships.error.message : 'Unknown error'}
          </p>
        )}
        {relationships.data && (
          <>
            <EventDistribution
              title="Most Connected Entities"
              buckets={relationships.data.most_connected}
            />
            <EventDistribution
              title="Entity Interaction Frequency (pairs)"
              buckets={relationships.data.interaction_frequency}
            />
          </>
        )}
      </div>
    </div>
  );
};
