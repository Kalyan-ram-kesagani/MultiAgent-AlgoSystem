import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { useTrading } from '../../context/TradingContext';
import { generateEquityCurve } from '../../data/mockData';

type Timeframe = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'All';

export const InteractiveEquityCurve: React.FC = () => {
  const { selectedAccountId, isAllAccounts, activeAccount, theme } = useTrading();
  const [timeframe, setTimeframe] = useState<Timeframe>('1M');

  const data = useMemo(() => {
    return generateEquityCurve(selectedAccountId, timeframe);
  }, [selectedAccountId, timeframe]);

  const timeframes: Timeframe[] = ['1D', '1W', '1M', '3M', '6M', '1Y', 'All'];

  // Current display point (latest)
  const latestDisplay = data[data.length - 1];

  // Determine if overall period trend is positive
  const positive = useMemo(() => {
    if (data.length <= 1) return true;
    return data[data.length - 1].equity >= data[0].equity;
  }, [data]);

  const formatCurrency = (val: number) =>
    `$${Number(val || 0).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;

  return (
    <div
      className={`p-4 sm:p-5 rounded-lg border transition-colors ${
        theme === 'dark'
          ? 'bg-slate-900/60 border-slate-800'
          : 'bg-white border-slate-200 shadow-xs'
      }`}
    >
      {/* Chart Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
        <div>
          <div className="flex items-center gap-2">
            <h2
              className={`text-sm font-semibold ${
                theme === 'dark' ? 'text-white' : 'text-slate-900'
              }`}
            >
              Equity & Balance Curve
            </h2>
            <span
              className={`text-[11px] font-mono ${
                theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
              }`}
            >
              {isAllAccounts ? 'Combined' : activeAccount?.account_name}
            </span>
          </div>
          {latestDisplay && (
            <div className="flex flex-wrap items-center gap-3 sm:gap-4 mt-1.5">
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-slate-500">Latest Equity:</span>
                <span className="text-xs font-semibold font-mono tabular-nums text-emerald-500">
                  ${latestDisplay.equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-slate-500">Balance:</span>
                <span
                  className={`text-xs font-medium font-mono tabular-nums ${
                    theme === 'dark' ? 'text-slate-200' : 'text-slate-800'
                  }`}
                >
                  ${latestDisplay.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-slate-500">DD:</span>
                <span className="text-xs font-mono tabular-nums text-amber-500">
                  {latestDisplay.drawdown}%
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Timeframe Selector (scrollable on mobile) */}
        <div
          className={`flex items-center p-0.5 rounded-md border overflow-x-auto max-w-full ${
            theme === 'dark'
              ? 'bg-slate-950/70 border-slate-800'
              : 'bg-slate-100 border-slate-200'
          }`}
        >
          {timeframes.map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-2 py-1 text-[11px] font-medium rounded transition-colors whitespace-nowrap cursor-pointer ${
                timeframe === tf
                  ? theme === 'dark'
                    ? 'bg-slate-800 text-white font-semibold shadow-xs'
                    : 'bg-white text-slate-900 font-semibold shadow-2xs'
                  : theme === 'dark'
                  ? 'text-slate-400 hover:text-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* User's Recharts Equity Curve Container */}
      <div className="mt-5 h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="0%"
                  stopColor={positive ? 'var(--color-profit)' : 'var(--color-loss)'}
                  stopOpacity={0.25}
                />
                <stop
                  offset="100%"
                  stopColor={positive ? 'var(--color-profit)' : 'var(--color-loss)'}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              minTickGap={40}
              tick={{ fontSize: 11, fill: 'var(--color-muted-foreground)' }}
            />
            <YAxis
              width={64}
              tickLine={false}
              axisLine={false}
              domain={['auto', 'auto']}
              tick={{ fontSize: 11, fill: 'var(--color-muted-foreground)' }}
              tickFormatter={(v: number) => `$${Math.round(v).toLocaleString()}`}
            />
            <Tooltip
              cursor={{ stroke: 'var(--color-border)' }}
              contentStyle={{
                background: 'var(--color-popover)',
                border: '1px solid var(--color-border)',
                borderRadius: 10,
                fontSize: 12,
                color: 'var(--color-popover-foreground)',
              }}
              labelStyle={{ color: 'var(--color-muted-foreground)' }}
              formatter={(value: any) => [formatCurrency(Number(value)), 'Equity']}
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke={positive ? 'var(--color-profit)' : 'var(--color-loss)'}
              strokeWidth={2}
              fill="url(#equityFill)"
              animationDuration={600}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
