import React, { useState } from 'react';
import { EventResponse } from '../../../types/api';
import { EventImpactDetails } from './EventImpactDetails';

interface EventImpactCardProps {
  seriesId: string;
  readerChapter: number;
  event: EventResponse;
}

export const EventImpactCard: React.FC<EventImpactCardProps> = ({ seriesId, readerChapter, event }) => {
  const [expanded, setExpanded] = useState(false);

  // We map basic description from the existing Timeline
  let description = `${event.type} involving ${event.subject_id}`;
  if (event.target_id) {
    description += ` and ${event.target_id}`;
  }
  if (event.metadata && event.metadata.description) {
    description = event.metadata.description;
  }

  return (
    <div style={{ border: '1px solid #e0e0e0', borderRadius: '8px', padding: '16px', marginBottom: '16px', backgroundColor: '#fff', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '1.1em', marginBottom: '4px' }}>
            Chapter {event.chapter_number}
          </div>
          <div style={{ color: '#2c3e50' }}>{description}</div>
        </div>
        
        <button 
          onClick={() => setExpanded(!expanded)}
          style={{ 
            padding: '6px 12px', 
            backgroundColor: expanded ? '#f8f9fa' : '#3498db', 
            color: expanded ? '#333' : 'white', 
            border: expanded ? '1px solid #ccc' : 'none', 
            borderRadius: '4px', 
            cursor: 'pointer',
            fontSize: '0.85em'
          }}
        >
          {expanded ? 'Collapse' : 'View Impact'}
        </button>
      </div>
      
      {expanded && (
        <EventImpactDetails 
          seriesId={seriesId} 
          eventId={event.id} 
          readerChapter={readerChapter} 
        />
      )}
    </div>
  );
};
