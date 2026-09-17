import React from 'react';
import { useImpactTimeline } from '../hooks/useImpactTimeline';
import { EventImpactDetails } from './EventImpactDetails';
import { ImpactAnalysisResultDTO } from '../../../types/api';

interface ImpactTimelineProps {
  seriesId: string;
  fromChapter: number;
  toChapter: number;
  readerChapter: number;
}

export const ImpactTimeline: React.FC<ImpactTimelineProps> = ({ seriesId, fromChapter, toChapter, readerChapter }) => {
  const { data: timelineData, isLoading, isError } = useImpactTimeline(seriesId, fromChapter, toChapter, readerChapter);

  if (isLoading) return <div style={{ padding: '16px', color: '#7f8c8d', fontStyle: 'italic' }}>Analyzing causal events...</div>;
  if (isError) return <div style={{ padding: '16px', color: '#e74c3c' }}>Failed to analyze impacts for this period.</div>;
  if (!timelineData || timelineData.length === 0) return <div style={{ padding: '16px', color: '#7f8c8d' }}>No impacting events found in this period.</div>;

  // Filter out events that actually have no impacts (e.g. they don't change state)
  const impactfulEvents = timelineData.filter((r: ImpactAnalysisResultDTO) => r.impacts.length > 0);

  if (impactfulEvents.length === 0) return <div style={{ padding: '16px', color: '#7f8c8d' }}>No events with measurable state changes found in this period.</div>;

  return (
    <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {impactfulEvents.map(result => (
        <div key={result.event_id} style={{ border: '1px solid #dcdde1', borderRadius: '8px', padding: '16px', backgroundColor: '#f9f9f9' }}>
          <div style={{ fontWeight: 'bold', fontSize: '1.1em', marginBottom: '8px', color: '#2c3e50' }}>
            Chapter {result.chapter} 
            <span style={{ fontSize: '0.7em', color: '#95a5a6', marginLeft: '8px' }}>ID: {result.event_id.slice(0,8)}</span>
          </div>
          
          <EventImpactDetails seriesId={seriesId} eventId={result.event_id} readerChapter={readerChapter} />
        </div>
      ))}
    </div>
  );
};
