import React, { InputHTMLAttributes } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({ label, error, style, id, ...rest }) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {label && (
        <label htmlFor={inputId} style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
          {label}
        </label>
      )}
      <input
        id={inputId}
        style={{
          backgroundColor: 'var(--tsi-surface-secondary)',
          color: 'var(--tsi-text-primary)',
          border: error ? '1px solid var(--tsi-status-error)' : '1px solid var(--tsi-border-default)',
          borderRadius: 'var(--tsi-radius-md)',
          padding: '8px 12px',
          fontSize: '0.875rem',
          outline: 'none',
          transition: 'border-color 0.15s ease',
          fontFamily: 'inherit',
          ...style,
        }}
        {...rest}
      />
      {error && <span style={{ fontSize: '0.75rem', color: 'var(--tsi-status-error)' }}>{error}</span>}
    </div>
  );
};
