import React, { useState } from 'react';
import { EventResponse } from '../../../types/api';
import { getEventCategory } from '../utils/timeline-utils';
import { EventDetails } from './EventDetails';

export const TimelineEventNode: React.FC<{ event: EventResponse }> = ({ event }) => {
  const [isOpen, setIsOpen] = useState(false);
  const category = getEventCategory(event.type);
  
  // Simple color mapping based on category for visual distinction
  const colors: Record<string, string> = {
    'Characters': '#3498db',
    'Power': '#e74c3c',
    'Factions': '#2ecc71',
    'Relationships': '#f1c40f',
    'All': '#95a5a6'
  };

  return (
    <div style={{ marginLeft: '24px', marginBottom: '12px' }}>
      <div 
        style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
        onClick={() => setIsOpen(!isOpen)}
        data-testid={`event-node-${event.id}`}
      >
        <span style={{ 
          display: 'inline-block', 
          width: '12px', 
          height: '12px', 
          borderRadius: '50%', 
          backgroundColor: colors[category] || colors['All'],
          marginRight: '8px' 
        }} />
        <span>{event.type.replace(/_/g, ' ')}</span>
      </div>
      {isOpen && <EventDetails event={event} onClose={() => setIsOpen(false)} />}
    </div>
  );
};
