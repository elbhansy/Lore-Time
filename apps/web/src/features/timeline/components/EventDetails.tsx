import React from 'react';
import { EventResponse } from '../../../types/api';

export const EventDetails: React.FC<{ event: EventResponse, onClose: () => void }> = ({ event, onClose }) => {
  return (
    <div style={{
      border: '1px solid #333', 
      padding: '16px', 
      marginTop: '8px',
      backgroundColor: '#f9f9f9',
      borderRadius: '4px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <strong>Event Details</strong>
        <button onClick={onClose} style={{ cursor: 'pointer' }}>X</button>
      </div>
      <p style={{ margin: '8px 0' }}>Type: {event.type}</p>
      <p style={{ margin: '4px 0' }}>Subject: {event.subject_type} ({event.subject_id})</p>
      {event.target_id && (
        <p style={{ margin: '4px 0' }}>Target: {event.target_type} ({event.target_id})</p>
      )}
      <details>
        <summary>Metadata</summary>
        <pre style={{ fontSize: '0.8em' }}>{JSON.stringify(event.metadata, null, 2)}</pre>
      </details>
    </div>
  );
};
