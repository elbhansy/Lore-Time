import React, { ReactNode } from 'react';

export interface ToolbarProps {
  children: ReactNode;
  actions?: ReactNode;
}

export const Toolbar: React.FC<ToolbarProps> = ({ children, actions }) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 16px',
        backgroundColor: 'var(--tsi-surface-primary)',
        borderBottom: '1px solid var(--tsi-border-subtle)',
        flexShrink: 0,
        gap: '12px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
        {children}
      </div>
      {actions && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {actions}
        </div>
      )}
    </div>
  );
};
