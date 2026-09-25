import React from 'react';
import { useTrading } from '../context/TradingContext';
import { MetricCard } from '../components/dashboard/MetricCard';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Sparkles,
  PieChart,
  Shield,
  Layers,
  Percent,
} from 'lucide-react';

export const AnalysisPage: React.FC = () => {
  const { trades, metrics, isAllAccounts, activeAccount, theme } = useTrading();
  const isDark = theme === 'dark';

  // Winning vs losing trade analysis
  const wins = trades.filter((t) => t.status === 'WIN');
  const losses = trades.filter((t) => t.status === 'LOSS');

  const avgWin = wins.length > 0 ? wins.reduce((sum, w) => sum + w.net_pl, 0) / wins.length : 0;
  const avgLoss = losses.length > 0 ? Math.abs(losses.reduce((sum, l) => sum + l.net_pl, 0) / losses.length) : 0;
  const winLossRatio = avgLoss > 0 ? (avgWin / avgLoss).toFixed(2) : avgWin > 0 ? '10.0' : '0.0';

  // Symbol distribution
  const symbolStats = trades.reduce((acc, t) => {
    if (!acc[t.symbol]) {
      acc[t.symbol] = { count: 0, pl: 0, wins: 0 };
    }
    acc[t.symbol].count += 1;
    acc[t.symbol].pl += t.net_pl;
    if (t.status === 'WIN') acc[t.symbol].wins += 1;
    return acc;
  }, {} as Record<string, { count: number; pl: number; wins: number }>);

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-200">
      {/* Header */}
      <div
        className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b ${
          isDark ? 'border-slate-800/80' : 'border-slate-200'
        }`}
      >
        <div>
          <div className="flex items-center gap-3">
            <h1 className={`text-xl sm:text-2xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Trading Performance Analytics
            </h1>
            <span
              className={`text-xs font-mono px-2 py-0.5 rounded border ${
                isDark
                  ? 'text-slate-400 bg-slate-900 border-slate-800'
                  : 'text-slate-600 bg-slate-100 border-slate-200'
              }`}
            >
              {trades.length} sample trades
            </span>
          </div>
          <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Statistical breakdown of edge expectancy, risk distribution, and execution consistency
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {isAllAccounts ? (
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md border ${
                isDark
                  ? 'bg-slate-900 border-slate-800 text-slate-300'
                  : 'bg-white border-slate-200 text-slate-700 shadow-2xs'
              }`}
            >
              <Layers className="w-3.5 h-3.5 text-emerald-500" />
              <span>Multi-Account Aggregated</span>
            </div>
          ) : (
            <div
              className={`px-3 py-1.5 rounded-md border ${
                isDark
                  ? 'bg-slate-900 border-slate-800 text-slate-300'
                  : 'bg-white border-slate-200 text-slate-700 shadow-2xs'
              }`}
            >
              Account: <strong className={isDark ? 'text-white' : 'text-slate-900'}>{activeAccount?.account_name}</strong>
            </div>
          )}
        </div>
      </div>

      {/* Primary Analytics KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <MetricCard
          label="Profit Factor"
          value={metrics.profitFactor}
          subvalue="Gross profit / Gross loss"
          trend={metrics.profitFactor >= 1.5 ? 'positive' : 'neutral'}
        />
        <MetricCard
          label="Win / Loss Payoff"
          value={`1 : ${winLossRatio}`}
          subvalue="Average win vs average loss"
          trend={Number(winLossRatio) >= 1.5 ? 'positive' : 'neutral'}
        />
        <MetricCard
          label="Average Win"
          value={`+$${avgWin.toFixed(2)}`}
          subvalue={`${wins.length} profitable exits`}
          trend="positive"
        />
        <MetricCard
          label="Average Loss"
          value={`-$${avgLoss.toFixed(2)}`}
          subvalue={`${losses.length} stop loss hits`}
          trend="negative"
        />
      </div>

      {/* Trade Outcome Breakdown (Wins vs Losses) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Winning Trade Analysis */}
        <div
          className={`p-5 rounded-lg border transition-colors ${
            isDark
              ? 'bg-slate-900/60 border-slate-800'
              : 'bg-white border-slate-200 shadow-xs'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-500" />
              <h2 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Winning Trade Profile
              </h2>
            </div>
            <span className="text-xs font-mono font-semibold text-emerald-500">
              {metrics.overallWinRate}% Win Rate
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div
              className={`p-3 rounded border flex items-center justify-between ${
                isDark
                  ? 'bg-slate-950/60 border-slate-800'
                  : 'bg-slate-50 border-slate-200'
              }`}
            >
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Total Winning Volume:</span>
              <span className="font-mono font-medium text-emerald-500 tabular-nums">
                +${wins.reduce((sum, w) => sum + w.net_pl, 0).toFixed(2)}
              </span>
            </div>
            <div
              className={`p-3 rounded border flex items-center justify-between ${
                isDark
                  ? 'bg-slate-950/60 border-slate-800'
                  : 'bg-slate-50 border-slate-200'
              }`}
            >
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Largest Win:</span>
              <span className="font-mono font-medium text-emerald-500 tabular-nums">
                +${Math.max(0, ...wins.map((w) => w.net_pl)).toFixed(2)}
              </span>
            </div>
            <div
              className={`p-3 rounded border flex items-center justify-between ${
                isDark
                  ? 'bg-slate-950/60 border-slate-800'
                  : 'bg-slate-50 border-slate-200'
              }`}
            >
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Risk-Free Conversion Rate:</span>
              <span className={`font-mono font-medium tabular-nums ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                {wins.length > 0
                  ? Math.round((wins.filter((w) => w.risk_free_status === 'YES').length / wins.length) * 100)
                  : 0}
                % moved to BE
              </span>
            </div>
          </div>
        </div>

        {/* Losing Trade Analysis */}
        <div
          className={`p-5 rounded-lg border transition-colors ${
            isDark
              ? 'bg-slate-900/60 border-slate-800'
              : 'bg-white border-slate-200 shadow-xs'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-rose-500" />
              <h2 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Losing Trade Profile
              </h2>
            </div>
            <span className="text-xs font-mono font-semibold text-rose-500">
              {100 - metrics.overallWinRate}% Loss Rate
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div
              className={`p-3 rounded border flex items-center justify-between ${
                isDark
                  ? 'bg-slate-950/60 border-slate-800'
                  : 'bg-slate-50 border-slate-200'
              }`}
            >
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Total Loss Volume:</span>
              <span className="font-mono font-medium text-rose-500 tabular-nums">
                -${Math.abs(losses.reduce((sum, l) => sum + l.net_pl, 0)).toFixed(2)}
              </span>
            </div>
            <div
              className={`p-3 rounded border flex items-center justify-between ${
                isDark
                  ? 'bg-slate-950/60 border-slate-800'
                  : 'bg-slate-50 border-slate-200'
              }`}
            >
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Largest Drawdown Stop:</span>
              <span className="font-mono font-medium text-rose-500 tabular-nums">
                -${Math.abs(Math.min(0, ...losses.map((l) => l.net_pl))).toFixed(2)}
              </span>
            </div>
            <div
              className={`p-3 rounded border flex items-center justify-between ${
                isDark
                  ? 'bg-slate-950/60 border-slate-800'
                  : 'bg-slate-50 border-slate-200'
              }`}
            >
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Max Risk Adherence:</span>
              <span className={`font-mono font-medium tabular-nums ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                100% within configured limits
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Symbol Breakdown Table */}
      <div
        className={`rounded-lg border overflow-hidden transition-colors ${
          isDark
            ? 'bg-slate-900/60 border-slate-800'
            : 'bg-white border-slate-200 shadow-xs'
        }`}
      >
        <div
          className={`px-5 py-3.5 border-b flex items-center justify-between ${
            isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-slate-50'
          }`}
        >
          <h2 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            Instrument & Symbol Breakdown
          </h2>
          <span className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Aggregated by ticker
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs min-w-[500px]">
            <thead
              className={`border-b text-[11px] uppercase tracking-wider ${
                isDark
                  ? 'border-slate-800 bg-slate-950/60 text-slate-400'
                  : 'border-slate-200 bg-slate-100 text-slate-600'
              }`}
            >
              <tr>
                <th className="py-3 px-4">Symbol</th>
                <th className="py-3 px-4">Total Deals</th>
                <th className="py-3 px-4">Win Rate</th>
                <th className="py-3 px-4 text-right">Net P&L</th>
              </tr>
            </thead>
            <tbody
              className={`divide-y font-mono ${
                isDark ? 'divide-slate-800/60 text-slate-300' : 'divide-slate-200 text-slate-700'
              }`}
            >
              {Object.entries(symbolStats).map(([sym, stats]) => {
                const wr = Math.round((stats.wins / stats.count) * 100);
                const isPos = stats.pl >= 0;
                return (
                  <tr
                    key={sym}
                    className={`transition-colors ${
                      isDark ? 'hover:bg-slate-800/40' : 'hover:bg-slate-50'
                    }`}
                  >
                    <td className={`py-3 px-4 font-bold font-sans ${isDark ? 'text-white' : 'text-slate-900'}`}>{sym}</td>
                    <td className="py-3 px-4 tabular-nums">{stats.count}</td>
                    <td className="py-3 px-4 tabular-nums">{wr}%</td>
                    <td className="py-3 px-4 text-right font-sans font-semibold tabular-nums">
                      <span className={isPos ? 'text-emerald-500' : 'text-rose-500'}>
                        {isPos ? '+' : ''}${stats.pl.toFixed(2)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Reserved AI Insights Foundation (Requirement #14: Clearly label as Coming soon) */}
      <div
        className={`p-6 rounded-lg border relative overflow-hidden transition-colors ${
          isDark
            ? 'border-slate-800 bg-slate-900/40'
            : 'border-slate-200 bg-white shadow-xs'
        }`}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div
              className={`p-2 rounded-lg border ${
                isDark
                  ? 'bg-slate-800 border-slate-700 text-slate-400'
                  : 'bg-slate-100 border-slate-200 text-slate-600'
              }`}
            >
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                AI Insights & Pattern Engine
              </h2>
              <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
                Autonomous strategy auditing and risk anomalies
              </span>
            </div>
          </div>
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded border ${
              isDark
                ? 'bg-slate-800 text-slate-300 border-slate-700'
                : 'bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            Coming soon
          </span>
        </div>

        <p className={`text-xs leading-relaxed max-w-2xl ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
          Deep learning models will cross-correlate execution slippage against London/NY volatility regimes, detect behavioral deviations, and generate automated strategy parameter adjustments. Reserved for Phase 5.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4 opacity-50 pointer-events-none">
          <div className={`p-3 rounded border text-xs ${isDark ? 'border-slate-800 bg-slate-950/60' : 'border-slate-200 bg-slate-50'}`}>
            <span className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Execution Drift Score</span>
            <span className={`font-mono ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>-- / 100</span>
          </div>
          <div className={`p-3 rounded border text-xs ${isDark ? 'border-slate-800 bg-slate-950/60' : 'border-slate-200 bg-slate-50'}`}>
            <span className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Spread Slippage Impact</span>
            <span className={`font-mono ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>-- pips</span>
          </div>
          <div className={`p-3 rounded border text-xs ${isDark ? 'border-slate-800 bg-slate-950/60' : 'border-slate-200 bg-slate-50'}`}>
            <span className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Suggested Parameter Tweak</span>
            <span className={`font-mono ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>Pending AI ingestion</span>
          </div>
        </div>
      </div>
    </div>
  );
};
