import React, { useState } from 'react';
import { useTrading } from '../context/TradingContext';
import { MetricCard } from '../components/dashboard/MetricCard';
import {
  Activity,
  Wifi,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Clock,
  Layers,
  AlertCircle,
  XCircle,
  CheckCircle,
  RefreshCw,
} from 'lucide-react';
import { OpenPosition } from '../types/trading';

export const LiveTradingPage: React.FC = () => {
  const {
    openPositions,
    metrics,
    activeAccount,
    isAllAccounts,
    syncStatus,
    dataMode,
    setDataMode,
    closePosition,
    syncNow,
    isSyncing,
    lastSync,
    theme,
  } = useTrading();

  const isDark = theme === 'dark';
  const [closingId, setClosingId] = useState<string | null>(null);

  const handleClose = async (posId: string) => {
    setClosingId(posId);
    try {
      await closePosition(posId);
    } finally {
      setClosingId(null);
    }
  };

  const sessions = [
    { name: 'London', status: 'OPEN', hours: '07:00 - 16:00 UTC', active: true },
    { name: 'New York', status: 'OPEN', hours: '13:00 - 21:00 UTC', active: true },
    { name: 'Tokyo', status: 'CLOSED', hours: '00:00 - 09:00 UTC', active: false },
    { name: 'Sydney', status: 'CLOSED', hours: '21:00 - 06:00 UTC', active: false },
  ];

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-200">
      {/* Top Header & Connection Bar */}
      <div
        className={`flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b ${
          isDark ? 'border-slate-800/80' : 'border-slate-200'
        }`}
      >
        <div>
          <div className="flex items-center gap-3">
            <h1 className={`text-xl sm:text-2xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Live Trading Console
            </h1>
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
              <span>Real-Time Stream</span>
            </div>
          </div>
          <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Active position monitoring, margin consumption, and manual order override
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          {/* Data Mode Switcher */}
          <div
            className={`flex items-center p-0.5 rounded-lg border text-xs ${
              isDark
                ? 'bg-slate-900 border-slate-800'
                : 'bg-slate-100 border-slate-200'
            }`}
          >
            <button
              onClick={() => setDataMode('live')}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                dataMode === 'live'
                  ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-300 font-semibold border border-emerald-500/40 shadow-xs'
                  : isDark
                  ? 'text-slate-400 hover:text-white'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Live Data
            </button>
            <button
              onClick={() => setDataMode('demo')}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                dataMode === 'demo'
                  ? 'bg-amber-500/20 text-amber-600 dark:text-amber-300 font-semibold border border-amber-500/40 shadow-xs'
                  : isDark
                  ? 'text-slate-400 hover:text-white'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Demo Mode
            </button>
          </div>

          <button
            onClick={syncNow}
            disabled={isSyncing}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md border transition-colors ${
              isDark
                ? 'text-slate-300 bg-slate-800 hover:bg-slate-700 border-slate-700'
                : 'text-slate-700 bg-white hover:bg-slate-100 border-slate-200 shadow-2xs'
            }`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin text-emerald-500' : ''}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Account Margin Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        <MetricCard
          label="Balance"
          value={`$${metrics.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
        />
        <MetricCard
          label="Equity"
          value={`$${metrics.equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          trend={metrics.equity >= metrics.balance ? 'positive' : 'negative'}
        />
        <MetricCard
          label="Used Margin"
          value={`$${metrics.margin.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
        />
        <MetricCard
          label="Free Margin"
          value={`$${metrics.freeMargin.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
        />
        <MetricCard
          label="Floating P&L"
          value={`${metrics.floatingPL >= 0 ? '+' : ''}$${metrics.floatingPL.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          trend={metrics.floatingPL >= 0 ? 'positive' : 'negative'}
          highlight
        />
      </div>

      {/* Market Sessions Monitor */}
      <div
        className={`p-4 rounded-lg border transition-colors ${
          isDark
            ? 'bg-slate-900/60 border-slate-800'
            : 'bg-white border-slate-200 shadow-xs'
        }`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-3">
          <span className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
            Global Market Sessions
          </span>
          <span className={`text-[11px] font-mono ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
            London & New York Overlap Active
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {sessions.map((sess) => (
            <div
              key={sess.name}
              className={`p-3 rounded border ${
                sess.active
                  ? isDark
                    ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                    : 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : isDark
                  ? 'bg-slate-900/40 border-slate-800 text-slate-500'
                  : 'bg-slate-50 border-slate-200 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{sess.name}</span>
                <span
                  className={`text-[10px] font-mono uppercase font-bold px-1.5 py-0.5 rounded ${
                    sess.active
                      ? isDark
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-emerald-200 text-emerald-800'
                      : isDark
                      ? 'bg-slate-800 text-slate-500'
                      : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  {sess.status}
                </span>
              </div>
              <span className={`text-[10px] font-mono block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{sess.hours}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Open Positions Table */}
      <div
        className={`rounded-lg border overflow-hidden transition-colors ${
          isDark
            ? 'bg-slate-900/60 border-slate-800'
            : 'bg-white border-slate-200 shadow-xs'
        }`}
      >
        <div
          className={`flex items-center justify-between px-4 sm:px-5 py-3.5 border-b ${
            isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-slate-50/80'
          }`}
        >
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-500" />
            <h2 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Active Positions
            </h2>
            <span className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
              ({openPositions.length})
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {isAllAccounts ? (
              <span className={`flex items-center gap-1 font-mono ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                <Layers className="w-3.5 h-3.5 text-emerald-500" />
                Aggregated across accounts
              </span>
            ) : (
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>
                Account: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{activeAccount?.account_name}</strong>
              </span>
            )}
          </div>
        </div>

        {openPositions.length === 0 ? (
          <div className="py-12 text-center text-xs">
            <p className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>No open positions currently active</p>
            <p className={`mt-1 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              Automated strategies are scanning markets for valid entry triggers.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs min-w-[700px]">
              <thead
                className={`border-b text-[11px] uppercase tracking-wider ${
                  isDark
                    ? 'border-slate-800 bg-slate-950/60 text-slate-400'
                    : 'border-slate-200 bg-slate-100 text-slate-600'
                }`}
              >
                <tr>
                  <th className="py-3 px-4">Ticket</th>
                  <th className="py-3 px-4">Symbol</th>
                  <th className="py-3 px-4">Direction</th>
                  <th className="py-3 px-4">Volume</th>
                  <th className="py-3 px-4">Entry</th>
                  <th className="py-3 px-4">Current Price</th>
                  <th className="py-3 px-4">SL / TP</th>
                  <th className="py-3 px-4">Risk-Free</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4 text-right">Floating P&L</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody
                className={`divide-y ${
                  isDark ? 'divide-slate-800/60 text-slate-300' : 'divide-slate-200 text-slate-700'
                }`}
              >
                {openPositions.map((pos: OpenPosition) => {
                  const isPositive = pos.floating_pl >= 0;
                  return (
                    <tr
                      key={pos.id}
                      className={`transition-colors group font-mono text-xs ${
                        isDark ? 'hover:bg-slate-800/40' : 'hover:bg-slate-50'
                      }`}
                    >
                      <td className={`py-3 px-4 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>#{pos.ticket}</td>
                      <td className={`py-3 px-4 font-bold font-sans ${isDark ? 'text-white' : 'text-slate-900'}`}>{pos.symbol}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`font-semibold px-2 py-0.5 rounded text-[11px] font-sans ${
                            pos.direction === 'BUY'
                              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                              : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30'
                          }`}
                        >
                          {pos.direction}
                        </span>
                      </td>
                      <td className="py-3 px-4 tabular-nums">{pos.volume.toFixed(2)}</td>
                      <td className="py-3 px-4 tabular-nums">{pos.entry_price.toFixed(5)}</td>
                      <td className={`py-3 px-4 font-bold tabular-nums ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                        {pos.current_price.toFixed(5)}
                      </td>
                      <td className={`py-3 px-4 text-[11px] tabular-nums ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        <span className="text-rose-500">{pos.stop_loss.toFixed(5)}</span>
                        {' / '}
                        <span className="text-emerald-500">{pos.take_profit.toFixed(5)}</span>
                      </td>
                      <td className="py-3 px-4 font-sans">
                        <span
                          className={`text-[11px] font-semibold px-1.5 py-0.5 rounded ${
                            pos.risk_free_status === 'YES'
                              ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40'
                              : isDark
                              ? 'bg-slate-800 text-slate-400'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          {pos.risk_free_status === 'YES' ? 'YES (BE Locked)' : 'NO'}
                        </span>
                      </td>
                      <td className={`py-3 px-4 font-sans text-[11px] ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        <div className="flex items-center gap-1">
                          <Clock className={`w-3 h-3 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
                          <span>{pos.duration}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-sans font-semibold tabular-nums text-sm">
                        <span className={isPositive ? 'text-emerald-500' : 'text-rose-500'}>
                          {isPositive ? '+' : ''}${pos.floating_pl.toFixed(2)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-sans">
                        <button
                          onClick={() => handleClose(pos.id)}
                          disabled={closingId === pos.id}
                          className="px-2.5 py-1 text-[11px] font-medium text-rose-600 dark:text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 rounded transition-colors disabled:opacity-50"
                        >
                          {closingId === pos.id ? 'Closing...' : 'Close'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
