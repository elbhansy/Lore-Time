import React, { useState } from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import {
  AssumptionType,
  CounterfactualAssumption,
} from '../../../api/contracts/read-models';

export interface TargetOption {
  id: string;
  name: string;
  type: 'CHARACTER' | 'EVENT';
  chapter?: number;
}

export interface ScenarioBuilderProps {
  readerChapter: number;
  availableTargets: TargetOption[];
  onExecuteScenario: (assumption: CounterfactualAssumption) => void;
  isExecuting: boolean;
}

export const ScenarioBuilder: React.FC<ScenarioBuilderProps> = ({
  readerChapter,
  availableTargets,
  onExecuteScenario,
  isExecuting,
}) => {
  const [assumptionType, setAssumptionType] = useState<AssumptionType>('ALTER_OUTCOME');
  const [selectedTargetId, setSelectedTargetId] = useState<string>(
    availableTargets.length > 0 ? availableTargets[0].id : ''
  );
  const [targetChapter, setTargetChapter] = useState<number>(Math.max(1, readerChapter));
  const [proposedValue, setProposedValue] = useState<string>('Survives the catastrophic event');
  const [justification, setJustification] = useState<string>(
    'What if the character evaded the fatal blow?'
  );

  const selectedTarget = availableTargets.find((t) => t.id === selectedTargetId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTargetId) return;

    onExecuteScenario({
      assumption_type: assumptionType,
      target_entity_id: selectedTargetId,
      target_entity_name: selectedTarget?.name || selectedTargetId,
      target_chapter: Math.min(targetChapter, readerChapter),
      proposed_value: proposedValue,
      justification: justification,
    });
  };

  return (
    <Card data-testid="scenario-builder" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
              Scenario Construction Engine
            </h2>
            <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
              Horizon Limit: Ch. {readerChapter}
            </Badge>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            Configure a hypothetical assumption strictly bounded by the current reader horizon.
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Intervention Category Selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--tsi-text-secondary)', textTransform: 'uppercase' }}>
            Intervention Category (Phase 5.0 Contract)
          </label>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {(['ALTER_OUTCOME', 'PREVENT_EVENT', 'INJECT_EVENT'] as AssumptionType[]).map((type) => {
              const isSelected = assumptionType === type;
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => setAssumptionType(type)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: 'var(--tsi-radius-md)',
                    border: isSelected ? '1px solid var(--tsi-accent-primary)' : '1px solid var(--tsi-border-subtle)',
                    backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'var(--tsi-surface-secondary)',
                    color: isSelected ? 'var(--tsi-text-primary)' : 'var(--tsi-text-secondary)',
                    fontSize: '0.8125rem',
                    fontWeight: isSelected ? 600 : 400,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {type.replace(/_/g, ' ')}
                </button>
              );
            })}
          </div>
        </div>

        {/* Target Entity & Chapter Selection */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--tsi-text-secondary)', textTransform: 'uppercase' }}>
              Target Entity / Character
            </label>
            <select
              data-testid="target-entity-select"
              value={selectedTargetId}
              onChange={(e) => setSelectedTargetId(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: 'var(--tsi-radius-md)',
                backgroundColor: 'var(--tsi-surface-secondary)',
                border: '1px solid var(--tsi-border-default)',
                color: 'var(--tsi-text-primary)',
                fontSize: '0.875rem',
                outline: 'none',
              }}
            >
              {availableTargets.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.type})
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--tsi-text-secondary)', textTransform: 'uppercase' }}>
              Intervention Chapter (Max: {readerChapter})
            </label>
            <input
              data-testid="intervention-chapter-input"
              type="number"
              min={1}
              max={readerChapter}
              value={targetChapter}
              onChange={(e) => setTargetChapter(Math.min(readerChapter, Math.max(1, parseInt(e.target.value, 10) || 1)))}
              style={{
                padding: '8px 12px',
                borderRadius: 'var(--tsi-radius-md)',
                backgroundColor: 'var(--tsi-surface-secondary)',
                border: '1px solid var(--tsi-border-default)',
                color: 'var(--tsi-text-primary)',
                fontSize: '0.875rem',
                outline: 'none',
              }}
            />
          </div>
        </div>

        {/* Proposed Value & Justification */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--tsi-text-secondary)', textTransform: 'uppercase' }}>
              Proposed Hypothetical Outcome
            </label>
            <input
              type="text"
              value={proposedValue}
              onChange={(e) => setProposedValue(e.target.value)}
              placeholder="e.g. Master Rank attained / Allegiance to Solar Order"
              style={{
                padding: '8px 12px',
                borderRadius: 'var(--tsi-radius-md)',
                backgroundColor: 'var(--tsi-surface-secondary)',
                border: '1px solid var(--tsi-border-default)',
                color: 'var(--tsi-text-primary)',
                fontSize: '0.875rem',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--tsi-text-secondary)', textTransform: 'uppercase' }}>
              Scenario Justification / Prompt
            </label>
            <input
              type="text"
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              placeholder="Hypothetical premise rationale"
              style={{
                padding: '8px 12px',
                borderRadius: 'var(--tsi-radius-md)',
                backgroundColor: 'var(--tsi-surface-secondary)',
                border: '1px solid var(--tsi-border-default)',
                color: 'var(--tsi-text-primary)',
                fontSize: '0.875rem',
                outline: 'none',
              }}
            />
          </div>
        </div>

        {/* Submit action */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
          <Button
            data-testid="apply-scenario-btn"
            type="submit"
            variant="primary"
            disabled={isExecuting || !selectedTargetId}
            style={{ minWidth: '180px' }}
          >
            {isExecuting ? 'Simulating Sandbox...' : 'Run What-If Simulation ↯'}
          </Button>
        </div>
      </form>
    </Card>
  );
};
