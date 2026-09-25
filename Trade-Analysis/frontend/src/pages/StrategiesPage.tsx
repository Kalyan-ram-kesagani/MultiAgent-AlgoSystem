import React, { useState } from 'react';
import { useTrading } from '../context/TradingContext';
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Archive,
  Layers,
  Shield,
  Clock,
  Sparkles,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { Strategy } from '../types/trading';

export const StrategiesPage: React.FC = () => {
  const { strategies, isAllAccounts, activeAccount, theme } = useTrading();
  const isDark = theme === 'dark';
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy>(strategies[0]);

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
              Automated Trading Strategies
            </h1>
            <span
              className={`text-xs font-mono px-2 py-0.5 rounded border ${
                isDark
                  ? 'text-slate-400 bg-slate-900 border-slate-800'
                  : 'text-slate-600 bg-slate-100 border-slate-200'
              }`}
            >
              {strategies.length} algorithms deployed
            </span>
          </div>
          <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Algorithmic rule sets, risk thresholds, version revisions, and execution metrics
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
              <span>Multi-Account Strategies</span>
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

      {/* Strategies Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {strategies.map((strat: Strategy) => {
          const isSelected = selectedStrategy?.id === strat.id;
          const isActive = strat.status === 'active';
          const isTesting = strat.status === 'testing';

          return (
            <div
              key={strat.id}
              onClick={() => setSelectedStrategy(strat)}
              className={`p-5 rounded-lg border transition-all cursor-pointer flex flex-col justify-between
                ${
                  isSelected
                    ? isDark
                      ? 'bg-slate-900/90 border-emerald-500/50 shadow-md ring-1 ring-emerald-500/20'
                      : 'bg-white border-emerald-500 shadow-md ring-1 ring-emerald-500/30'
                    : isDark
                    ? 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
                    : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
                }
              `}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className={`text-sm font-semibold tracking-tight flex items-center gap-1.5 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                      <span>{strat.name}</span>
                      <span className={`text-xs font-mono ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{strat.version}</span>
                    </h3>
                  </div>

                  <span
                    className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded tracking-wider ${
                      isActive
                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                        : isTesting
                        ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30'
                        : isDark
                        ? 'bg-slate-800 text-slate-400 border border-slate-700'
                        : 'bg-slate-100 text-slate-600 border border-slate-200'
                    }`}
                  >
                    {strat.status}
                  </span>
                </div>

                <p className={`text-xs line-clamp-2 mb-4 leading-relaxed ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                  {strat.description}
                </p>

                <div
                  className={`grid grid-cols-2 gap-2 text-xs p-3 rounded border mb-3 ${
                    isDark
                      ? 'bg-slate-950/60 border-slate-800/80'
                      : 'bg-slate-50 border-slate-200'
                  }`}
                >
                  <div>
                    <span className={`text-[10px] block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Win Rate</span>
                    <span className="font-semibold font-mono text-emerald-500 tabular-nums">
                      {strat.win_rate}%
                    </span>
                  </div>
                  <div>
                    <span className={`text-[10px] block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Net P&L</span>
                    <span
                      className={`font-semibold font-mono tabular-nums ${
                        strat.profit_loss >= 0 ? 'text-emerald-500' : 'text-rose-500'
                      }`}
                    >
                      {strat.profit_loss >= 0 ? '+' : ''}${strat.profit_loss.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className={`text-[10px] block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Max DD</span>
                    <span className="font-mono text-amber-500 tabular-nums">
                      {strat.max_drawdown}%
                    </span>
                  </div>
                  <div>
                    <span className={`text-[10px] block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Trades</span>
                    <span className={`font-mono tabular-nums ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                      {strat.total_trades}
                    </span>
                  </div>
                </div>
              </div>

              <div className={`flex items-center justify-between pt-2 border-t text-[11px] ${isDark ? 'border-slate-800 text-slate-400' : 'border-slate-200 text-slate-500'}`}>
                <span>Created {strat.created_date}</span>
                <span className="text-emerald-500 font-medium flex items-center gap-1">
                  View Specs <ChevronRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Strategy Deep-Dive Details */}
      {selectedStrategy && (
        <div
          className={`p-4 sm:p-6 rounded-lg border space-y-6 transition-colors ${
            isDark
              ? 'bg-slate-900/60 border-slate-800'
              : 'bg-white border-slate-200 shadow-xs'
          }`}
        >
          <div
            className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b ${
              isDark ? 'border-slate-800' : 'border-slate-200'
            }`}
          >
            <div>
              <div className="flex items-center gap-2.5">
                <Cpu className="w-5 h-5 text-emerald-500" />
                <h2 className={`text-base font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  {selectedStrategy.name} ({selectedStrategy.version})
                </h2>
              </div>
              <p className={`text-xs mt-1 max-w-2xl ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                {selectedStrategy.description}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Status:</span>
              <span
                className={`text-xs font-semibold px-2.5 py-1 rounded uppercase tracking-wider border ${
                  isDark
                    ? 'bg-slate-800 text-slate-200 border-slate-700'
                    : 'bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                {selectedStrategy.status}
              </span>
            </div>
          </div>

          {/* Strategy Rules & Risk Parameters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            {/* Rules */}
            <div className="space-y-3">
              <h3 className={`text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                Algorithmic Execution Rules
              </h3>
              <div
                className={`p-4 rounded-lg border space-y-2 ${
                  isDark
                    ? 'bg-slate-950/60 border-slate-800/80'
                    : 'bg-slate-50 border-slate-200'
                }`}
              >
                {selectedStrategy.rules.map((rule, idx) => (
                  <div key={idx} className={`flex items-start gap-2 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                    <span className="font-mono text-emerald-500 font-semibold">{idx + 1}.</span>
                    <span className="leading-relaxed">{rule}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Risk Parameters */}
            <div className="space-y-3">
              <h3 className={`text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                <Shield className="w-4 h-4 text-emerald-500" />
                Risk Parameters & Protection
              </h3>
              <div
                className={`p-4 rounded-lg border space-y-2.5 ${
                  isDark
                    ? 'bg-slate-950/60 border-slate-800/80'
                    : 'bg-slate-50 border-slate-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Max Risk Per Trade:</span>
                  <span className={`font-mono font-medium ${isDark ? 'text-white' : 'text-slate-900'}`}>
                    {selectedStrategy.risk_parameters.max_risk_per_trade}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Max Daily Drawdown:</span>
                  <span className="font-mono font-medium text-amber-500">
                    {selectedStrategy.risk_parameters.max_daily_drawdown}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Target Risk-to-Reward:</span>
                  <span className="font-mono font-medium text-emerald-500">
                    {selectedStrategy.risk_parameters.rr_target}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Breakeven (Risk-Free) Trigger:</span>
                  <span className={`font-mono font-medium ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                    {selectedStrategy.risk_parameters.breakeven_trigger}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Version History */}
          <div className="space-y-3 pt-2">
            <h3 className={`text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
              <Clock className="w-4 h-4 text-slate-400" />
              Version Revision History
            </h3>
            <div
              className={`divide-y border rounded-lg overflow-hidden text-xs ${
                isDark
                  ? 'divide-slate-800/80 border-slate-800 bg-slate-950/40'
                  : 'divide-slate-200 border-slate-200 bg-slate-50'
              }`}
            >
              {selectedStrategy.version_history.map((vh, i) => (
                <div key={i} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`font-mono font-bold px-2 py-0.5 rounded border ${
                        isDark
                          ? 'text-white bg-slate-800 border-slate-700'
                          : 'text-slate-900 bg-white border-slate-300'
                      }`}
                    >
                      {vh.version}
                    </span>
                    <span className={isDark ? 'text-slate-300' : 'text-slate-700'}>{vh.changes}</span>
                  </div>
                  <span className={`text-[11px] font-mono whitespace-nowrap ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                    {vh.date}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Reserved AI Strategy Evolution (Requirement #16 & #17) */}
          <div
            className={`p-4 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
              isDark
                ? 'border-slate-800 bg-slate-900/30'
                : 'border-slate-200 bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Sparkles className="w-5 h-5 text-slate-400" />
              <div>
                <h4 className={`text-xs font-semibold ${isDark ? 'text-slate-300' : 'text-slate-800'}`}>
                  AI-Assisted Strategy Generation
                </h4>
                <p className={`text-[11px] ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
                  Autonomous backtesting & parameter refinement architecture ready for Phase 7
                </p>
              </div>
            </div>
            <span
              className={`text-xs font-medium px-2.5 py-1 rounded border self-start sm:self-auto ${
                isDark
                  ? 'text-slate-400 bg-slate-800 border-slate-700'
                  : 'text-slate-600 bg-slate-200 border-slate-300'
              }`}
            >
              Coming soon
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
