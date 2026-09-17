import React from 'react';
import { Button } from '../../../components/ui/Button';

export interface DiscoveryItem {
  id: string;
  label: string;
  chapter?: number | null;
  typeBadge?: string;
}

export interface CausalInvestigationControlsProps {
  mode: 'EVENT' | 'CHARACTER';
  onModeChange: (mode: 'EVENT' | 'CHARACTER') => void;
  items: DiscoveryItem[];
  selectedId: string | null;
  onSelectId: (id: string) => void;
  searchQuery: string;
  onSearchQueryChange: (q: string) => void;
  isLoadingDiscovery?: boolean;
}

export const CausalInvestigationControls: React.FC<CausalInvestigationControlsProps> = ({
  mode,
  onModeChange,
  items,
  selectedId,
  onSelectId,
  searchQuery,
  onSearchQueryChange,
  isLoadingDiscovery = false,
}) => {
  return (
    <div
      data-testid="causal-investigation-controls"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        padding: '14px 18px',
        backgroundColor: 'var(--tsi-surface-primary)',
        border: '1px solid var(--tsi-border-subtle)',
        borderRadius: 'var(--tsi-radius-md)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '0.6875rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              color: 'var(--tsi-text-muted)',
            }}
          >
            Target Mode:
          </span>
          <div style={{ display: 'flex', gap: '4px' }}>
            <Button
              size="sm"
              variant={mode === 'EVENT' ? 'primary' : 'ghost'}
              onClick={() => onModeChange('EVENT')}
              data-testid="mode-switch-event"
              style={{ padding: '3px 10px', fontSize: '0.75rem' }}
            >
              Event
            </Button>
            <Button
              size="sm"
              variant={mode === 'CHARACTER' ? 'primary' : 'ghost'}
              onClick={() => onModeChange('CHARACTER')}
              data-testid="mode-switch-character"
              style={{ padding: '3px 10px', fontSize: '0.75rem' }}
            >
              Character
            </Button>
          </div>
        </div>

        {/* Local Search Filter over loaded discovery items */}
        <div style={{ position: 'relative', minWidth: '220px' }}>
          <input
            type="text"
            role="searchbox"
            aria-label={`Filter ${mode.toLowerCase()} targets`}
            placeholder={`Filter ${mode.toLowerCase()} targets...`}
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            style={{
              width: '100%',
              padding: '5px 10px',
              backgroundColor: 'var(--tsi-surface-secondary)',
              border: '1px solid var(--tsi-border-default)',
              borderRadius: 'var(--tsi-radius-md)',
              color: 'var(--tsi-text-primary)',
              fontSize: '0.8125rem',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
          {searchQuery && (
            <button
              onClick={() => onSearchQueryChange('')}
              aria-label="Clear filter"
              style={{
                position: 'absolute',
                right: '6px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'transparent',
                border: 'none',
                color: 'var(--tsi-text-muted)',
                cursor: 'pointer',
                fontSize: '0.75rem',
              }}
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Target Selector Dropdown */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <label
          htmlFor="causal-target-select"
          style={{
            fontSize: '0.75rem',
            color: 'var(--tsi-text-secondary)',
            whiteSpace: 'nowrap',
          }}
        >
          Investigate Specific {mode === 'EVENT' ? 'Event' : 'Character'}:
        </label>
        <select
          id="causal-target-select"
          data-testid="causal-target-select"
          disabled={isLoadingDiscovery || items.length === 0}
          value={selectedId || ''}
          onChange={(e) => onSelectId(e.target.value)}
          style={{
            flex: 1,
            padding: '6px 10px',
            backgroundColor: 'var(--tsi-surface-secondary)',
            border: '1px solid var(--tsi-border-default)',
            borderRadius: 'var(--tsi-radius-sm)',
            color: 'var(--tsi-text-primary)',
            fontSize: '0.8125rem',
            outline: 'none',
            cursor: 'pointer',
          }}
        >
          <option value="">-- Overview (Full Topology) --</option>
          {items.map((it) => (
            <option key={it.id} value={it.id}>
              {it.chapter != null ? `[Ch. ${it.chapter}] ` : ''}
              {it.label}
              {it.typeBadge ? ` (${it.typeBadge})` : ''}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};
