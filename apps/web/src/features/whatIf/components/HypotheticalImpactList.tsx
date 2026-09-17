import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { FormattedHypotheticalImpact } from '../whatIfAdapters';

export interface HypotheticalImpactListProps {
  impacts: FormattedHypotheticalImpact[];
  onInspectEntity?: (impact: FormattedHypotheticalImpact) => void;
}

export const HypotheticalImpactList: React.FC<HypotheticalImpactListProps> = ({
  impacts,
  onInspectEntity,
}) => {
  const getSigVariant = (sig: string) => {
    switch (sig) {
      case 'CRITICAL':
        return 'error';
      case 'HIGH':
        return 'warning';
      default:
        return 'neutral';
    }
  };

  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
              Impacted Entities Analysis
            </h3>
            <Badge variant="warning" style={{ fontSize: '0.625rem' }}>
              SIMULATED CONSEQUENCES
            </Badge>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            Entities whose state, rank, allegiance, or survival diverges from canon in this scenario ({impacts.length} total).
          </span>
        </div>
      </div>

      <div
        data-testid="hypothetical-impact-list"
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          maxHeight: '340px',
          overflowY: 'auto',
        }}
      >
        {impacts.map((impact) => (
          <div
            key={impact.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              backgroundColor: 'var(--tsi-surface-secondary)',
              border: '1px solid var(--tsi-border-subtle)',
              borderRadius: 'var(--tsi-radius-md)',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Badge variant={getSigVariant(impact.significance)} style={{ fontSize: '0.6875rem' }}>
                {impact.significance}
              </Badge>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--tsi-text-primary)' }}>
                  {impact.entityName} ({impact.entityType})
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-secondary)' }}>
                  Property: {impact.changedProperty}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8125rem' }}>
                <span style={{ color: 'var(--tsi-text-muted)', textDecoration: 'line-through' }}>
                  {impact.canonicalValue}
                </span>
                <span style={{ color: 'var(--tsi-status-warning)', fontWeight: 600 }}>
                  → {impact.hypotheticalValue}
                </span>
              </div>

              {onInspectEntity && (
                <button
                  type="button"
                  onClick={() => onInspectEntity(impact)}
                  style={{
                    background: 'transparent',
                    border: '1px solid var(--tsi-border-default)',
                    color: 'var(--tsi-text-primary)',
                    padding: '4px 8px',
                    borderRadius: 'var(--tsi-radius-sm)',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                  }}
                >
                  Inspect ↗
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
