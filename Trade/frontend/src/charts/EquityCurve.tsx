import { useMemo, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import type { EquityPoint } from '@/types';
import { cn, formatCurrency } from '@/utils/format';

interface EquityCurveProps {
  data: EquityPoint[];
}

const filters = ['1D', '1W', '1M', '3M', '6M', '1Y', 'All'] as const;
type Filter = (typeof filters)[number];

function filterData(data: EquityPoint[], filter: Filter): EquityPoint[] {
  if (filter === 'All') return data;

  const now = new Date();
  let start: Date;

  switch (filter) {
    case '1D':
      start = new Date(now.getTime() - 86400000);
      break;
    case '1W':
      start = new Date(now.getTime() - 7 * 86400000);
      break;
    case '1M':
      start = new Date(now.getTime() - 30 * 86400000);
      break;
    case '3M':
      start = new Date(now.getTime() - 90 * 86400000);
      break;
    case '6M':
      start = new Date(now.getTime() - 180 * 86400000);
      break;
    case '1Y':
      start = new Date(now.getTime() - 365 * 86400000);
      break;
    default:
      return data;
  }

  return data.filter((d) => new Date(d.date) >= start);
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.[0]) return null;

  return (
    <div className="bg-surface-overlay border border-border rounded-lg px-3 py-2 shadow-lg">
      <p className="text-xs text-text-muted mb-0.5">{label}</p>
      <p className="text-sm font-semibold text-text-primary">
        {formatCurrency(payload[0].value).replace('+', '')}
      </p>
    </div>
  );
}

export function EquityCurve({ data }: EquityCurveProps) {
  const [filter, setFilter] = useState<Filter>('3M');
  const filtered = useMemo(() => filterData(data, filter), [data, filter]);

  const isPositive =
    filtered.length >= 2 &&
    filtered[filtered.length - 1].equity >= filtered[0].equity;

  const gradientColor = isPositive ? '#22c55e' : '#ef4444';
  const strokeColor = isPositive ? '#22c55e' : '#ef4444';

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-text-primary">Equity Curve</h3>
        <div className="flex items-center gap-0.5 bg-surface-overlay rounded-lg p-0.5">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                'px-2.5 py-1 text-[11px] font-medium rounded-md transition-all duration-150',
                filter === f
                  ? 'bg-surface-raised text-text-primary shadow-sm'
                  : 'text-text-muted hover:text-text-secondary'
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={filtered} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={gradientColor} stopOpacity={0.15} />
                <stop offset="100%" stopColor={gradientColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              tickFormatter={(val) => {
                const d = new Date(val);
                return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
              }}
              interval="preserveStartEnd"
              minTickGap={60}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              tickFormatter={(val) => `$${(val / 1000).toFixed(1)}k`}
              domain={['auto', 'auto']}
              width={50}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="equity"
              stroke={strokeColor}
              strokeWidth={1.5}
              fill="url(#equityGradient)"
              animationDuration={600}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
