import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useReader } from '../../reader/reader-store';
import { useSearchSuggestions } from '../hooks/useGlobalSearch';
import { SearchType } from '../types';

export const GlobalSearch: React.FC = () => {
  const { seriesId, readerChapter } = useReader();
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const navigate = useNavigate();
  
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  const { data: suggestions, isLoading } = useSearchSuggestions(seriesId, debouncedQuery, readerChapter);

  const handleSelect = (id: string, type: SearchType) => {
    setQuery('');
    // Navigation logic respecting readerChapter
    let path = `/series/${seriesId}`;
    switch (type) {
      case SearchType.CHARACTER:
        path += `/characters/${id}`;
        break;
      case SearchType.FACTION:
        path += `/factions/${id}`;
        break;
      case SearchType.SKILL:
        // Assume skills tab/profile exists
        path += `?tab=skills&skillId=${id}`;
        break;
      case SearchType.RANK:
      case SearchType.POWER_SYSTEM:
        path += `?tab=power`;
        break;
      case SearchType.EVENT:
        path += `?tab=timeline&eventId=${id}`;
        break;
    }
    // Deep linking must retain the reader perspective
    navigate(path);
  };

  return (
    <div style={{ position: 'relative', width: '300px' }}>
      <input
        type="text"
        placeholder="🔎 Search characters, factions..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
      />
      {query.length >= 2 && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, background: 'white',
          border: '1px solid #ccc', borderRadius: '4px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          zIndex: 1000, maxHeight: '300px', overflowY: 'auto'
        }}>
          {isLoading ? (
            <div style={{ padding: '8px' }}>Searching...</div>
          ) : suggestions && suggestions.length > 0 ? (
            suggestions.map(s => (
              <div 
                key={s.id}
                onClick={() => handleSelect(s.id, s.type)}
                style={{ padding: '8px', cursor: 'pointer', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between' }}
              >
                <span>{s.title}</span>
                <span style={{ fontSize: '0.8em', color: '#888' }}>{s.type}</span>
              </div>
            ))
          ) : (
            <div style={{ padding: '8px', color: '#888' }}>No results found</div>
          )}
        </div>
      )}
    </div>
  );
};
