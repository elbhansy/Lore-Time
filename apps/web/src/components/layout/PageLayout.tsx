import React, { ReactNode } from 'react';

export interface PageLayoutProps {
  title: string;
  subtitle?: string;
  toolbar?: ReactNode;
  children: ReactNode;
}

export const PageLayout: React.FC<PageLayoutProps> = ({
  title,
  subtitle,
  toolbar,
  children,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
      <div
        style={{
          padding: '24px 32px 16px',
          borderBottom: toolbar ? 'none' : '1px solid var(--tsi-border-subtle)',
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: '1.5rem',
            fontWeight: 700,
            color: 'var(--tsi-text-primary)',
            letterSpacing: '-0.02em',
          }}
        >
          {title}
        </h1>
        {subtitle && (
          <p
            style={{
              margin: '4px 0 0',
              fontSize: '0.875rem',
              color: 'var(--tsi-text-secondary)',
            }}
          >
            {subtitle}
          </p>
        )}
      </div>

      {toolbar}

      <div style={{ padding: '24px 32px', flex: 1, overflowY: 'auto' }}>
        {children}
      </div>
    </div>
  );
};
