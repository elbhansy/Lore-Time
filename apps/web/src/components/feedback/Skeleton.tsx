import React from 'react';

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '1rem',
  borderRadius = 'var(--tsi-radius-sm)',
  style,
}) => {
  return (
    <div
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: 'var(--tsi-surface-secondary)',
        backgroundImage: 'linear-gradient(90deg, var(--tsi-surface-secondary) 0px, var(--tsi-surface-elevated) 50%, var(--tsi-surface-secondary) 100%)',
        backgroundSize: '200px 100%',
        animation: 'skeleton-shimmer 1.5s infinite',
        ...style,
      }}
    />
  );
};
