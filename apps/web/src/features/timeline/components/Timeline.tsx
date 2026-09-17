import React from 'react';
import { EventExplorer } from '../../event-query/components/EventExplorer';

export const Timeline: React.FC<{ totalChapters: number }> = ({ totalChapters }) => {
  return (
    <div style={{ marginTop: '32px' }}>
      <EventExplorer />
    </div>
  );
};
