import React, { ReactNode } from 'react';

export interface VisualizationViewportProps {
  toolbar?: ReactNode;
  legend?: ReactNode;
  inspector?: ReactNode;
  children: ReactNode;
}

export const VisualizationViewport: React.FC<VisualizationViewportProps> = ({
  toolbar,
  legend,
  inspector,
  children,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        height: '100%',
        position: 'relative',
        backgroundColor: 'var(--tsi-canvas)',
        overflow: 'hidden',
      }}
    >
      {toolbar}

      <div style={{ display: 'flex', flex: 1, position: 'relative', overflow: 'hidden' }}>
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          {children}

          {legend && (
            <div
              style={{
                position: 'absolute',
                bottom: '16px',
                left: '16px',
                zIndex: 30,
                backgroundColor: 'var(--tsi-surface-primary)',
                border: '1px solid var(--tsi-border-default)',
                borderRadius: 'var(--tsi-radius-md)',
                padding: '8px 12px',
                boxShadow: 'var(--tsi-shadow-md)',
              }}
            >
              {legend}
            </div>
          )}
        </div>

        {inspector}
      </div>
    </div>
  );
};
