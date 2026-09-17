import React, { HTMLAttributes } from 'react';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
}

export const Card: React.FC<CardProps> = ({ elevated = false, children, style, ...rest }) => {
  const baseStyle: React.CSSProperties = {
    backgroundColor: elevated ? 'var(--tsi-surface-elevated)' : 'var(--tsi-surface-primary)',
    border: '1px solid var(--tsi-border-subtle)',
    borderRadius: 'var(--tsi-radius-md)',
    padding: 'var(--tsi-space-md)',
    boxShadow: elevated ? 'var(--tsi-shadow-md)' : 'var(--tsi-shadow-sm)',
    ...style,
  };

  return (
    <div style={baseStyle} {...rest}>
      {children}
    </div>
  );
};
