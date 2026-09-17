import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { CounterfactualScenarioDTO } from '../../../api/contracts/read-models';

export interface ScenarioSummaryProps {
  scenario: CounterfactualScenarioDTO | null;
  readerChapter: number;
}

export const ScenarioSummary: React.FC<ScenarioSummaryProps> = ({
  scenario,
  readerChapter,
}) => {
  if (!scenario) {
    return (
      <Card
        style={{
          padding: '14px 18px',
          backgroundColor: 'var(--tsi-surface-primary)',
          border: '1px solid var(--tsi-border-subtle)',
          fontSize: '0.8125rem',
          color: 'var(--tsi-text-muted)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span>No hypothetical scenario currently active. Configure an intervention above to simulate.</span>
        <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
          Canonical Horizon: Ch. {readerChapter}
        </Badge>
      </Card>
    );
  }

  const { assumption } = scenario;

  return (
    <Card
      data-testid="scenario-summary-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        padding: '16px 20px',
        backgroundColor: 'var(--tsi-surface-elevated)',
        border: '1px solid var(--tsi-status-warning)',
        borderRadius: 'var(--tsi-radius-lg)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Badge variant="warning" style={{ fontSize: '0.6875rem' }}>
            HYPOTHETICAL SCENARIO ACTIVE
          </Badge>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            Branch ID: {scenario.scenario_id}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
            Intervention @ Ch. {assumption.target_chapter}
          </Badge>
          <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
            Simulated Through Ch. {readerChapter}
          </Badge>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          alignItems: 'center',
          gap: '16px',
          padding: '14px 16px',
          backgroundColor: 'var(--tsi-surface-secondary)',
          borderRadius: 'var(--tsi-radius-md)',
          border: '1px solid var(--tsi-border-subtle)',
        }}
      >
        {/* Canonical Base State */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Canonical State
          </span>
          <span style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--tsi-text-primary)' }}>
            {assumption.target_entity_name || assumption.target_entity_id}
          </span>
          <span style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
            Historical timeline event / canonical trajectory
          </span>
        </div>

        {/* Transition indicator */}
        <div style={{ fontSize: '1.25rem', color: 'var(--tsi-status-warning)', fontWeight: 700 }}>
          ↯
        </div>

        {/* Hypothetical Alternative */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-status-warning)', textTransform: 'uppercase' }}>
            Hypothetical Assumption ({assumption.assumption_type.replace(/_/g, ' ')})
          </span>
          <span style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--tsi-status-warning)' }}>
            {assumption.proposed_value || 'Outcome Altered'}
          </span>
          <span style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-muted)' }}>
            {assumption.justification}
          </span>
        </div>
      </div>
    </Card>
  );
};
