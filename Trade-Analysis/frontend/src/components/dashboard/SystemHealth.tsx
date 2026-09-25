import React from 'react';
import { useTrading } from '../../context/TradingContext';

export const SystemHealth: React.FC = () => {
  const { systemHealth, pingMs, theme } = useTrading();
  const isDark = theme === 'dark';

  return (
    <div
      className={`p-4 sm:p-5 rounded-lg border transition-colors ${
        isDark
          ? 'bg-slate-900/60 border-slate-800'
          : 'bg-white border-slate-200 shadow-xs'
      }`}
    >
      <div className="flex items-center justify-between mb-3.5">
        <h2 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
          System Health
        </h2>
        <span
          className={`text-[11px] font-mono ${
            isDark ? 'text-emerald-400' : 'text-emerald-600'
          }`}
        >
          All Nodes Active
        </span>
      </div>

      <div className="space-y-2.5">
        {systemHealth.map((item) => {
          const isComingSoon = item.status === 'coming_soon';
          const isOk = item.status === 'ok';

          return (
            <div
              key={item.id}
              className={`flex items-center justify-between py-1 text-xs border-b last:border-0 ${
                isDark ? 'border-slate-800/40' : 'border-slate-100'
              }`}
            >
              <span className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                {item.name}
              </span>

              <div className="flex items-center gap-2">
                {item.latency_ms && !isComingSoon && (
                  <span
                    className={`text-[10px] font-mono tabular-nums ${
                      isDark ? 'text-slate-500' : 'text-slate-400'
                    }`}
                  >
                    {item.latency_ms}ms
                  </span>
                )}

                {isComingSoon ? (
                  <span
                    className={`text-[11px] font-medium px-2 py-0.5 rounded border ${
                      isDark
                        ? 'text-slate-500 bg-slate-800/80 border-slate-700/60'
                        : 'text-slate-500 bg-slate-100 border-slate-200'
                    }`}
                  >
                    Coming Soon
                  </span>
                ) : isOk ? (
                  <div
                    className={`flex items-center gap-1.5 font-mono font-medium text-[11px] ${
                      isDark ? 'text-emerald-400' : 'text-emerald-600'
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        isDark ? 'bg-emerald-400' : 'bg-emerald-500'
                      }`}
                    />
                    <span>OK</span>
                  </div>
                ) : (
                  <div
                    className={`flex items-center gap-1.5 font-mono font-medium text-[11px] ${
                      isDark ? 'text-amber-400' : 'text-amber-600'
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        isDark ? 'bg-amber-400' : 'bg-amber-500'
                      }`}
                    />
                    <span>WARN</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
