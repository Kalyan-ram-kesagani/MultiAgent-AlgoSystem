import React from 'react';
import { useTrading } from '../context/TradingContext';
import { MetricCard } from '../components/dashboard/MetricCard';
import { InteractiveEquityCurve } from '../components/dashboard/InteractiveEquityCurve';
import { RecentActivity } from '../components/dashboard/RecentActivity';
import { SystemHealth } from '../components/dashboard/SystemHealth';
import { RiskStatus } from '../components/dashboard/RiskStatus';
import { ShieldCheck, Activity, Layers, Calendar, Globe2 } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { metrics, isAllAccounts, activeAccount, syncStatus, lastSync, theme } = useTrading();
  const isDark = theme === 'dark';

  // Active trading session determination (UTC based)
  const getActiveSessions = () => {
    const hour = new Date().getUTCHours();
    const sessions = [];
    if (hour >= 0 && hour < 9) sessions.push('Tokyo');
    if (hour >= 7 && hour < 16) sessions.push('London');
    if (hour >= 13 && hour < 21) sessions.push('New York');
    if (sessions.length === 0) sessions.push('Sydney');
    return sessions.join(' / ');
  };

  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-200">
      {/* 1. Dashboard Header */}
      <div
        className={`flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b ${
          isDark ? 'border-slate-800/80' : 'border-slate-200'
        }`}
      >
        <div>
          <span className={`text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Good morning
          </span>
          <div className="flex items-center gap-3 mt-0.5">
            <h1 className={`text-xl sm:text-2xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Trading System
            </h1>
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>MT5 Connected</span>
            </div>
          </div>
        </div>

        <div className={`flex flex-wrap items-center gap-2 sm:gap-3 text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border ${
              isDark
                ? 'bg-slate-900/60 border-slate-800 text-slate-300'
                : 'bg-white border-slate-200 shadow-2xs text-slate-700'
            }`}
          >
            <Calendar className={`w-3.5 h-3.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
            <span>{currentDate}</span>
          </div>

          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border ${
              isDark
                ? 'bg-slate-900/60 border-slate-800 text-slate-300'
                : 'bg-white border-slate-200 shadow-2xs text-slate-700'
            }`}
          >
            <Globe2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>Session: <strong className={isDark ? 'text-slate-200' : 'text-slate-900'}>{getActiveSessions()}</strong></span>
          </div>

          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border ${
              isDark
                ? 'bg-slate-900/60 border-slate-800'
                : 'bg-white border-slate-200 shadow-2xs'
            }`}
          >
            {isAllAccounts ? (
              <span className={`flex items-center gap-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                <Layers className="w-3.5 h-3.5 text-emerald-500" />
                Aggregated Multi-Account
              </span>
            ) : (
              <span className={isDark ? 'text-slate-300' : 'text-slate-700'}>
                Context: <strong className={isDark ? 'text-white' : 'text-slate-900'}>{activeAccount?.account_name}</strong>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 2. Today's Metrics Grid */}
      <div>
        <div className={`text-[11px] font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
          Today's Performance
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <MetricCard
            label="Today's P&L"
            value={`${metrics.todayPL >= 0 ? '+' : ''}$${metrics.todayPL.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
            subvalue={`${metrics.winningTrades} wins · ${metrics.losingTrades} losses`}
            trend={metrics.todayPL >= 0 ? 'positive' : 'negative'}
            highlight
          />
          <MetricCard
            label="Today's Trades"
            value={metrics.todayTrades}
            subvalue="Active execution window"
          />
          <MetricCard
            label="Today's Win Rate"
            value={`${metrics.todayWinRate}%`}
            subvalue="Calculated on closed deals"
            trend={metrics.todayWinRate >= 50 ? 'positive' : 'negative'}
          />
          <MetricCard
            label="Current Drawdown"
            value={`${metrics.drawdown}%`}
            subvalue="From current session peak"
            trend={metrics.drawdown > 3 ? 'negative' : 'neutral'}
          />
        </div>
      </div>

      {/* 3. Account Metrics Grid */}
      <div>
        <div className={`text-[11px] font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
          Account Balance & Margins
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <MetricCard
            label="Balance"
            value={`$${metrics.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
            subvalue="Settled funds"
          />
          <MetricCard
            label="Equity"
            value={`$${metrics.equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
            subvalue="Balance + Floating P&L"
            trend={metrics.equity >= metrics.balance ? 'positive' : 'negative'}
          />
          <MetricCard
            label="Floating P&L"
            value={`${metrics.floatingPL >= 0 ? '+' : ''}$${metrics.floatingPL.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
            subvalue="Open positions running"
            trend={metrics.floatingPL >= 0 ? 'positive' : 'negative'}
          />
          <MetricCard
            label="Free Margin"
            value={`$${metrics.freeMargin.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
            subvalue="Available for new risk"
          />
        </div>
      </div>

      {/* 4. Large Interactive Equity Curve */}
      <InteractiveEquityCurve />

      {/* 5. Recent Activity (Replacing Recent Trades as requested by Requirement #1) */}
      <RecentActivity />

      {/* 6. System Health & Risk Status (Side by Side Grid) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SystemHealth />
        <RiskStatus />
      </div>
    </div>
  );
};
