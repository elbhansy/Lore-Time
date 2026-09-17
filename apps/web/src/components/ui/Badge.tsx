import React, { HTMLAttributes } from 'react';

export type BadgeVariant = 'default' | 'neutral' | 'success' | 'warning' | 'error' | 'temporal';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantStyles: Record<BadgeVariant, React.CSSProperties> = {
  default: {
    backgroundColor: 'rgba(99, 102, 241, 0.15)',
    color: '#818cf8',
    borderColor: 'rgba(99, 102, 241, 0.3)',
  },
  neutral: {
    backgroundColor: 'var(--tsi-surface-secondary)',
    color: 'var(--tsi-text-secondary)',
    borderColor: 'var(--tsi-border-default)',
  },
  success: {
    backgroundColor: 'var(--tsi-status-success-bg)',
    color: 'var(--tsi-status-success)',
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  warning: {
    backgroundColor: 'var(--tsi-status-warning-bg)',
    color: 'var(--tsi-status-warning)',
    borderColor: 'rgba(245, 158, 11, 0.3)',
  },
  error: {
    backgroundColor: 'var(--tsi-status-error-bg)',
    color: 'var(--tsi-status-error)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  temporal: {
    backgroundColor: 'var(--tsi-temporal-scope-glow)',
    color: 'var(--tsi-temporal-scope)',
    borderColor: 'rgba(217, 119, 6, 0.4)',
  },
};

export const Badge: React.FC<BadgeProps> = ({ variant = 'default', children, style, ...rest }) => {
  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '2px 8px',
    fontSize: '0.75rem',
    fontWeight: 500,
    borderRadius: 'var(--tsi-radius-full)',
    border: '1px solid',
    lineHeight: 1.3,
    ...variantStyles[variant],
    ...style,
  };

  return (
    <span style={baseStyle} {...rest}>
      {children}
    </span>
  );
};
