import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  trend?: 'positive' | 'negative' | 'neutral';
  icon?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  trend = 'neutral',
  icon,
}) => {
  const getTrendColor = () => {
    if (trend === 'positive') return 'var(--accent-green)';
    if (trend === 'negative') return 'var(--accent-red)';
    return 'var(--text-muted)';
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {label}
        </span>
        {icon && <span style={{ color: 'var(--accent-cyan)' }}>{icon}</span>}
      </div>
      <div style={{ fontSize: '1.65rem', fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.02em' }}>
        {value}
      </div>

      {subtext && (
        <span style={{ fontSize: '0.75rem', color: getTrendColor() }}>
          {subtext}
        </span>
      )}
    </div>
  );
};
