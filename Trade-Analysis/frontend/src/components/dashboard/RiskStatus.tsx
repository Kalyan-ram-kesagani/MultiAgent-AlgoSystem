import React from 'react';
import { useTrading } from '../../context/TradingContext';
import { ShieldCheck, AlertTriangle, Lock } from 'lucide-react';

export const RiskStatus: React.FC = () => {
  const { riskStatus, activeAccount, isAllAccounts, theme } = useTrading();
  const isDark = theme === 'dark';

  const { daily_risk_percent, daily_limit_percent, status } = riskStatus;

  const getStatusBadge = () => {
    switch (status) {
      case 'locked':
        return (
          <div className="flex items-center gap-1.5 text-rose-500 font-medium text-xs">
            <Lock className="w-3.5 h-3.5" />
            <span>Trading Locked</span>
          </div>
        );
      case 'approaching':
        return (
          <div className="flex items-center gap-1.5 text-amber-500 font-medium text-xs">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Risk Limit Approaching</span>
          </div>
        );
      case 'within_limit':
      default:
        return (
          <div className="flex items-center gap-1.5 text-emerald-500 font-medium text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Within Limit</span>
          </div>
        );
    }
  };

  const usagePercent = Math.min(100, Math.round((daily_risk_percent / daily_limit_percent) * 100));

  return (
    <div
      className={`p-4 sm:p-5 rounded-lg border transition-colors ${
        isDark
          ? 'bg-slate-900/60 border-slate-800'
          : 'bg-white border-slate-200 shadow-xs'
      }`}
    >
      <div className="flex items-center justify-between mb-3.5">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <h2 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            Risk Status
          </h2>
        </div>
        <span className={`text-[11px] font-mono ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
          {isAllAccounts ? 'Aggregated Limits' : activeAccount?.account_name}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div
          className={`p-2.5 rounded border ${
            isDark
              ? 'bg-slate-800/40 border-slate-800'
              : 'bg-slate-50 border-slate-200'
          }`}
        >
          <span className={`text-[11px] block mb-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Daily Risk
          </span>
          <span
            className={`text-lg font-semibold font-sans tabular-nums ${
              isDark ? 'text-slate-100' : 'text-slate-900'
            }`}
          >
            {daily_risk_percent.toFixed(1)}%
          </span>
        </div>

        <div
          className={`p-2.5 rounded border ${
            isDark
              ? 'bg-slate-800/40 border-slate-800'
              : 'bg-slate-50 border-slate-200'
          }`}
        >
          <span className={`text-[11px] block mb-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Daily Limit
          </span>
          <span
            className={`text-lg font-semibold font-sans tabular-nums ${
              isDark ? 'text-slate-100' : 'text-slate-900'
            }`}
          >
            {daily_limit_percent.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className={`flex justify-between text-[11px] mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
          <span>Daily Risk Utilization</span>
          <span className="font-mono tabular-nums">{usagePercent}%</span>
        </div>
        <div className={`w-full h-1.5 rounded-full overflow-hidden ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`}>
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              status === 'locked'
                ? 'bg-rose-500'
                : status === 'approaching'
                ? 'bg-amber-400'
                : 'bg-emerald-500'
            }`}
            style={{ width: `${usagePercent}%` }}
          />
        </div>
      </div>

      <div className={`flex items-center justify-between pt-2 border-t ${isDark ? 'border-slate-800/60' : 'border-slate-200'}`}>
        <span className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Status</span>
        {getStatusBadge()}
      </div>
    </div>
  );
};
