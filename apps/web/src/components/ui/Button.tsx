import React, { ButtonHTMLAttributes } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
}

const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
  primary: {
    backgroundColor: 'var(--tsi-accent-primary)',
    color: '#ffffff',
    border: '1px solid var(--tsi-accent-primary)',
  },
  secondary: {
    backgroundColor: 'var(--tsi-surface-secondary)',
    color: 'var(--tsi-text-primary)',
    border: '1px solid var(--tsi-border-default)',
  },
  ghost: {
    backgroundColor: 'transparent',
    color: 'var(--tsi-text-secondary)',
    border: '1px solid transparent',
  },
  danger: {
    backgroundColor: 'var(--tsi-status-error-bg)',
    color: 'var(--tsi-status-error)',
    border: '1px solid var(--tsi-status-error)',
  },
};

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: {
    padding: '4px 8px',
    fontSize: '0.8125rem',
    borderRadius: 'var(--tsi-radius-sm)',
  },
  md: {
    padding: '8px 14px',
    fontSize: '0.875rem',
    borderRadius: 'var(--tsi-radius-md)',
  },
  lg: {
    padding: '10px 18px',
    fontSize: '1rem',
    borderRadius: 'var(--tsi-radius-md)',
  },
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'secondary',
  size = 'md',
  isLoading = false,
  disabled,
  children,
  style,
  ...rest
}) => {
  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '6px',
    fontWeight: 500,
    cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
    opacity: disabled || isLoading ? 0.5 : 1,
    transition: 'all 0.15s ease',
    fontFamily: 'inherit',
    ...variantStyles[variant],
    ...sizeStyles[size],
    ...style,
  };

  return (
    <button disabled={disabled || isLoading} style={baseStyle} {...rest}>
      {isLoading && <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⟳</span>}
      {children}
    </button>
  );
};
