import React from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  ArrowRightLeft,
  Wifi,
  WifiOff,
  RefreshCw,
  Sliders,
  AlertTriangle,
  Play,
  Square,
  Lock,
  Layers,
} from 'lucide-react';
import { useTrading } from '../../context/TradingContext';
import { ActivityType, SystemActivity } from '../../types/trading';

export const RecentActivity: React.FC = () => {
  const { recentActivities, isAllAccounts, theme } = useTrading();
  const isDark = theme === 'dark';

  const getActivityIcon = (type: ActivityType, level?: string) => {
    switch (type) {
      case 'trade_opened':
        return <TrendingUp className="w-4 h-4 text-emerald-500" />;
      case 'trade_closed':
        return <TrendingDown className="w-4 h-4 text-sky-500" />;
      case 'risk_free_activated':
        return <ShieldCheck className="w-4 h-4 text-emerald-500" />;
      case 'sl_modified':
      case 'tp_modified':
        return <Sliders className="w-4 h-4 text-amber-500" />;
      case 'mt5_connected':
        return <Wifi className="w-4 h-4 text-emerald-500" />;
      case 'mt5_disconnected':
        return <WifiOff className="w-4 h-4 text-rose-500" />;
      case 'mt5_synchronized':
        return <RefreshCw className="w-4 h-4 text-blue-500" />;
      case 'account_switched':
        return <ArrowRightLeft className={`w-4 h-4 ${isDark ? 'text-slate-400' : 'text-slate-500'}`} />;
      case 'strategy_enabled':
        return <Play className="w-4 h-4 text-emerald-500" />;
      case 'strategy_disabled':
        return <Square className={`w-4 h-4 ${isDark ? 'text-slate-400' : 'text-slate-500'}`} />;
      case 'risk_limit_reached':
        return <Lock className="w-4 h-4 text-rose-500" />;
      case 'system_warning':
      default:
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
    }
  };

  const getActivityBadgeColor = (type: ActivityType) => {
    switch (type) {
      case 'trade_closed':
        return isDark ? 'text-sky-400' : 'text-sky-600';
      case 'risk_free_activated':
        return isDark ? 'text-emerald-400 font-semibold' : 'text-emerald-600 font-semibold';
      case 'trade_opened':
        return isDark ? 'text-emerald-400' : 'text-emerald-600';
      case 'mt5_connected':
      case 'mt5_synchronized':
        return isDark ? 'text-blue-400' : 'text-blue-600';
      case 'risk_limit_reached':
      case 'mt5_disconnected':
        return isDark ? 'text-rose-400 font-semibold' : 'text-rose-600 font-semibold';
      case 'system_warning':
        return isDark ? 'text-amber-400' : 'text-amber-600';
      default:
        return isDark ? 'text-slate-300' : 'text-slate-700';
    }
  };

  return (
    <div
      className={`p-4 sm:p-5 rounded-lg border transition-colors ${
        isDark
          ? 'bg-slate-900/60 border-slate-800'
          : 'bg-white border-slate-200 shadow-xs'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            Recent Activity
          </h2>
          <span className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            · System Events
          </span>
        </div>
        <span
          className={`text-[11px] font-mono ${
            isDark ? 'text-slate-500' : 'text-slate-400'
          }`}
        >
          {recentActivities.length} events logged
        </span>
      </div>

      {recentActivities.length === 0 ? (
        <div
          className={`py-8 text-center text-xs ${
            isDark ? 'text-slate-500' : 'text-slate-400'
          }`}
        >
          No recent activity events recorded.
        </div>
      ) : (
        <div
          className={`divide-y ${
            isDark ? 'divide-slate-800/80' : 'divide-slate-200'
          }`}
        >
          {recentActivities.slice(0, 7).map((activity: SystemActivity) => (
            <div
              key={activity.id}
              className={`py-3 first:pt-0 last:pb-0 flex items-start justify-between gap-3 group px-2 -mx-2 rounded transition-colors ${
                isDark
                  ? 'hover:bg-slate-800/20'
                  : 'hover:bg-slate-50'
              }`}
            >
              <div className="flex items-start gap-3 min-w-0">
                <div
                  className={`mt-0.5 p-1.5 rounded-md border shrink-0 ${
                    isDark
                      ? 'bg-slate-800/80 border-slate-700/60'
                      : 'bg-slate-100 border-slate-200'
                  }`}
                >
                  {getActivityIcon(activity.type, activity.level)}
                </div>

                <div className="flex flex-col min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs ${getActivityBadgeColor(activity.type)}`}>
                      {activity.title}
                    </span>
                    {activity.symbol && (
                      <span
                        className={`text-[11px] font-mono font-medium ${
                          isDark ? 'text-slate-300' : 'text-slate-700'
                        }`}
                      >
                        {activity.symbol}
                      </span>
                    )}
                    {isAllAccounts && (
                      <span
                        className={`text-[10px] font-mono flex items-center gap-1 ${
                          isDark ? 'text-slate-400' : 'text-slate-500'
                        }`}
                      >
                        <Layers className="w-2.5 h-2.5" />
                        {activity.account_name}
                      </span>
                    )}
                  </div>

                  <p
                    className={`text-xs mt-0.5 break-words ${
                      isDark ? 'text-slate-300' : 'text-slate-600'
                    }`}
                  >
                    {activity.description}
                  </p>
                </div>
              </div>

              <div className="flex flex-col items-end shrink-0 text-right">
                <span
                  className={`text-[11px] font-sans whitespace-nowrap ${
                    isDark ? 'text-slate-400' : 'text-slate-500'
                  }`}
                >
                  {activity.relative_time}
                </span>
                {activity.pl !== undefined && (
                  <span
                    className={`text-xs font-mono font-medium tabular-nums ${
                      activity.pl >= 0
                        ? isDark
                          ? 'text-emerald-400'
                          : 'text-emerald-600'
                        : isDark
                        ? 'text-rose-400'
                        : 'text-rose-600'
                    }`}
                  >
                    {activity.pl >= 0 ? '+' : ''}${activity.pl.toFixed(2)}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
