import React, { useState } from 'react';
import { useReader } from '../../reader/reader-store';
import { useEventQuery } from '../hooks/useEventQuery';

export const EventExplorer: React.FC = () => {
  const { seriesId, readerChapter } = useReader();
  const [fromChapter, setFromChapter] = useState(1);
  const [toChapter, setToChapter] = useState(readerChapter);
  const [type, setType] = useState('');
  const [subjectId, setSubjectId] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 50;

  // Sync toChapter with readerChapter if readerChapter changes and is smaller
  React.useEffect(() => {
    if (toChapter > readerChapter) setToChapter(readerChapter);
  }, [readerChapter, toChapter]);

  const { data, isLoading, isError, error } = useEventQuery({
    seriesId,
    readerChapter,
    fromChapter,
    toChapter,
    type: type || undefined,
    subjectId: subjectId || undefined,
    page,
    pageSize
  });

  return (
    <div style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '16px', background: '#fff' }}>
      <h3>Event Explorer</h3>
      <div style={{ display: 'flex', gap: '16px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.9em', color: '#555' }}>From Chapter:</label>
          <input type="number" min="1" max={toChapter} value={fromChapter} onChange={e => setFromChapter(Number(e.target.value))} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.9em', color: '#555' }}>To Chapter:</label>
          <input type="number" min={fromChapter} max={readerChapter} value={toChapter} onChange={e => setToChapter(Number(e.target.value))} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.9em', color: '#555' }}>Type:</label>
          <select value={type} onChange={e => setType(e.target.value)}>
            <option value="">All Types</option>
            <option value="CHARACTER_INTRODUCED">CHARACTER_INTRODUCED</option>
            <option value="CHARACTER_DIED">CHARACTER_DIED</option>
            <option value="POWER_RANK_CHANGED">POWER_RANK_CHANGED</option>
            <option value="SKILL_UNLOCKED">SKILL_UNLOCKED</option>
            <option value="FACTION_MEMBER_JOINED">FACTION_MEMBER_JOINED</option>
            <option value="RELATIONSHIP_CREATED">RELATIONSHIP_CREATED</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.9em', color: '#555' }}>Subject ID:</label>
          <input type="text" value={subjectId} onChange={e => setSubjectId(e.target.value)} placeholder="e.g. char1" />
        </div>
      </div>

      <hr style={{ border: 'none', borderTop: '1px solid #eee', margin: '16px 0' }} />

      {isLoading && <p>Loading events...</p>}
      {isError && <p style={{ color: 'red' }}>Error: {(error as any).message}</p>}
      {data && (
        <>
          <div style={{ marginBottom: '16px', fontSize: '0.9em', color: '#7f8c8d' }}>
            Found {data.total} events (Page {data.page})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {data.items.map(evt => (
              <div key={evt.id} style={{ display: 'flex', padding: '12px', borderLeft: '4px solid #3498db', background: '#f8f9fa', borderRadius: '0 4px 4px 0' }}>
                <div style={{ width: '80px', fontWeight: 'bold', color: '#34495e' }}>Ch. {evt.chapter_id.replace('c', '')}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 'bold' }}>{evt.type}</div>
                  <div style={{ fontSize: '0.9em', color: '#555' }}>Subject: {evt.subject_id} {evt.target_id ? `| Target: ${evt.target_id}` : ''}</div>
                </div>
              </div>
            ))}
            {data.items.length === 0 && <p style={{ color: '#888' }}>No events found in this range.</p>}
          </div>

          <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
            <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</button>
            <button disabled={!data.has_next} onClick={() => setPage(p => p + 1)}>Next</button>
          </div>
        </>
      )}
    </div>
  );
};
