import React from 'react';
import { useTrading } from '../../context/TradingContext';

interface MetricCardProps {
  label: string;
  value: string | number;
  subvalue?: string;
  trend?: 'positive' | 'negative' | 'neutral';
  highlight?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subvalue,
  trend = 'neutral',
  highlight = false,
}) => {
  const { theme } = useTrading();

  const getTrendColor = () => {
    if (trend === 'positive') return 'text-emerald-500 dark:text-emerald-400';
    if (trend === 'negative') return 'text-rose-500 dark:text-rose-400';
    return theme === 'dark' ? 'text-slate-100' : 'text-slate-900';
  };

  return (
    <div
      className={`p-3.5 sm:p-4 rounded-lg border transition-all duration-150 ${
        theme === 'dark'
          ? highlight
            ? 'bg-slate-900/90 border-slate-700/80 shadow-xs'
            : 'bg-slate-900/60 border-slate-800 hover:border-slate-700/60'
          : highlight
          ? 'bg-white border-emerald-500/40 shadow-xs ring-1 ring-emerald-500/10'
          : 'bg-white border-slate-200 hover:border-slate-300 shadow-2xs'
      }`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span
          className={`text-xs font-medium tracking-normal ${
            theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
          }`}
        >
          {label}
        </span>
      </div>

      <div className="flex items-baseline gap-2">
        {/* Clean, normal professional numerical font with tabular figures */}
        <span
          className={`text-xl sm:text-2xl font-semibold tracking-tight font-sans tabular-nums ${getTrendColor()}`}
        >
          {value}
        </span>
      </div>

      {subvalue && (
        <div
          className={`mt-1 text-[11px] font-sans tracking-tight truncate ${
            theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
          }`}
        >
          {subvalue}
        </div>
      )}
    </div>
  );
};

