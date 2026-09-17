import React from 'react';
import { EventDistributionDTO, EventStatisticsDTO } from '../types';

const sectionStyle: React.CSSProperties = { marginBottom: '24px' };

export const OverviewPanel: React.FC<{ statistics: EventStatisticsDTO }> = ({ statistics }) => (
  <div style={sectionStyle}>
    <div style={{ display: 'flex', gap: '24px', marginBottom: '16px' }}>
      <div>
        <strong style={{ fontSize: '28px', display: 'block' }}>{statistics.total_events}</strong>
        Total Events
      </div>
      <div>
        <strong style={{ fontSize: '28px', display: 'block' }}>{statistics.chapters}</strong>
        Chapters
      </div>
    </div>
  </div>
);

/** Sorted bar list — no chart library (M3.0 non-goal). Longest bar first,
 * matching the API's deterministic count DESC ordering. */
export const EventDistribution: React.FC<{
  title: string;
  buckets: EventDistributionDTO[];
  emptyMessage?: string;
  formatKey?: (key: string) => string;
}> = ({ title, buckets, emptyMessage, formatKey }) => {
  const max = buckets.length > 0 ? Math.max(...buckets.map((b) => b.count)) : 0;
  return (
    <div style={sectionStyle}>
      <h4 style={{ margin: '0 0 8px 0' }}>{title}</h4>
      {buckets.length === 0 ? (
        <p style={{ color: '#888' }}>{emptyMessage ?? 'No data in this scope.'}</p>
      ) : (
        <div style={{ maxHeight: '240px', overflowY: 'auto' }}>
          {buckets.map((b) => (
            <div key={b.key} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ width: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flexShrink: 0 }} title={b.key}>
                {formatKey ? formatKey(b.key) : b.key}
              </span>
              <div
                style={{
                  height: '14px',
                  width: `${max > 0 ? (b.count / max) * 100 : 0}%`,
                  minWidth: b.count > 0 ? '2px' : 0,
                  backgroundColor: '#3498db',
                  borderRadius: '2px',
                }}
                aria-hidden
              />
              <span style={{ marginLeft: 'auto', fontVariantNumeric: 'tabular-nums' }}>{b.count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
