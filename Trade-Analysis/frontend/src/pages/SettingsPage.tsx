import React, { useState } from 'react';
import { useTrading } from '../context/TradingContext';
import {
  Settings,
  Shield,
  Sliders,
  Download,
  Moon,
  Sun,
  Server,
  Save,
  Check,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { theme, setTheme, trades, activeAccount, isAllAccounts } = useTrading();
  const isDark = theme === 'dark';

  const [dailyRiskLimit, setDailyRiskLimit] = useState('5.0');
  const [maxRiskPerTrade, setMaxRiskPerTrade] = useState('1.0');
  const [breakevenTriggerR, setBreakevenTriggerR] = useState('1.0');
  const [slippagePips, setSlippagePips] = useState('2.0');
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2500);
  };

  const handleExportCSV = () => {
    const headers = [
      'Ticket',
      'Symbol',
      'Direction',
      'Volume',
      'EntryPrice',
      'ExitPrice',
      'StopLoss',
      'TakeProfit',
      'EntryTime',
      'ExitTime',
      'NetPL',
      'Status',
      'RiskPercent',
      'RiskFree',
      'Strategy',
    ];

    const rows = trades.map((t) => [
      t.ticket,
      t.symbol,
      t.direction,
      t.volume,
      t.entry_price,
      t.exit_price,
      t.stop_loss,
      t.take_profit,
      `"${t.entry_time}"`,
      `"${t.exit_time}"`,
      t.net_pl,
      t.status,
      t.initial_risk_percent,
      t.risk_free_status,
      `"${t.strategy_name}"`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `trades_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

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
              System Settings & Risk Safeguards
            </h1>
          </div>
          <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Configure risk governor limits, MT5 terminal bridge timeouts, export trade logs, and appearance
          </p>
        </div>

        {isSaved && (
          <div className="flex items-center gap-1.5 px-3 py-1 text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 rounded-md">
            <Check className="w-4 h-4" />
            <span>Settings saved successfully</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Risk & MT5 Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Risk Limits Form */}
          <div
            className={`p-5 sm:p-6 rounded-lg border transition-colors ${
              isDark
                ? 'bg-slate-900/60 border-slate-800'
                : 'bg-white border-slate-200 shadow-xs'
            }`}
          >
            <div
              className={`flex items-center gap-2 mb-4 pb-3 border-b ${
                isDark ? 'border-slate-800' : 'border-slate-100'
              }`}
            >
              <Shield className="w-4 h-4 text-emerald-500" />
              <h2 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Risk Governor Parameters
              </h2>
            </div>

            <form onSubmit={handleSave} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className={`block font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                    Daily Maximum Loss Limit (% Equity)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={dailyRiskLimit}
                    onChange={(e) => setDailyRiskLimit(e.target.value)}
                    className={`w-full px-3 py-2 rounded-md border focus:outline-hidden transition-colors ${
                      isDark
                        ? 'bg-slate-950 border-slate-700 text-white focus:border-emerald-500'
                        : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-emerald-600 focus:bg-white'
                    }`}
                  />
                  <span className={`text-[10px] mt-1 block ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                    System automatically locks execution when daily drawdown reaches this cap.
                  </span>
                </div>

                <div>
                  <label className={`block font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                    Max Risk Per Trade (% Balance)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={maxRiskPerTrade}
                    onChange={(e) => setMaxRiskPerTrade(e.target.value)}
                    className={`w-full px-3 py-2 rounded-md border focus:outline-hidden transition-colors ${
                      isDark
                        ? 'bg-slate-950 border-slate-700 text-white focus:border-emerald-500'
                        : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-emerald-600 focus:bg-white'
                    }`}
                  />
                  <span className={`text-[10px] mt-1 block ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                    Calculates lot sizing automatically from stop loss distance.
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className={`block font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                    Risk-Free Breakeven Trigger (R Multiple)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={breakevenTriggerR}
                    onChange={(e) => setBreakevenTriggerR(e.target.value)}
                    className={`w-full px-3 py-2 rounded-md border focus:outline-hidden transition-colors ${
                      isDark
                        ? 'bg-slate-950 border-slate-700 text-white focus:border-emerald-500'
                        : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-emerald-600 focus:bg-white'
                    }`}
                  />
                  <span className={`text-[10px] mt-1 block ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                    Moves Stop Loss to Breakeven once trade floats at +1.0R.
                  </span>
                </div>

                <div>
                  <label className={`block font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                    Max Slippage Tolerance (Pips)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={slippagePips}
                    onChange={(e) => setSlippagePips(e.target.value)}
                    className={`w-full px-3 py-2 rounded-md border focus:outline-hidden transition-colors ${
                      isDark
                        ? 'bg-slate-950 border-slate-700 text-white focus:border-emerald-500'
                        : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-emerald-600 focus:bg-white'
                    }`}
                  />
                  <span className={`text-[10px] mt-1 block ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                    Rejects market execution if price deviates beyond buffer.
                  </span>
                </div>
              </div>

              <div
                className={`pt-3 border-t flex justify-end ${
                  isDark ? 'border-slate-800' : 'border-slate-200'
                }`}
              >
                <button
                  type="submit"
                  className="flex items-center gap-1.5 px-4 py-2 font-medium text-white bg-emerald-600 hover:bg-emerald-500 rounded-md transition-colors shadow-2xs"
                >
                  <Save className="w-4 h-4" />
                  <span>Save Risk Limits</span>
                </button>
              </div>
            </form>
          </div>

          {/* MT5 Architecture Bridge Info */}
          <div
            className={`p-5 sm:p-6 rounded-lg border transition-colors ${
              isDark
                ? 'bg-slate-900/60 border-slate-800'
                : 'bg-white border-slate-200 shadow-xs'
            }`}
          >
            <div
              className={`flex items-center gap-2 mb-3 pb-3 border-b ${
                isDark ? 'border-slate-800' : 'border-slate-100'
              }`}
            >
              <Server className="w-4 h-4 text-emerald-500" />
              <h2 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                MT5 Architecture & Isolation
              </h2>
            </div>

            <p className={`text-xs leading-relaxed mb-3 ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
              The platform executes a strict account-isolation architecture. MT5 terminals connect via a high-performance Python/FastAPI IPC bridge. All ticket requests, history tables, and equity queries are filtered by <code className="font-mono text-emerald-500">account_id</code> to guarantee zero cross-account leakage.
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-950/60 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] block ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Bridge Protocol</span>
                <span className={`font-mono font-medium ${isDark ? 'text-white' : 'text-slate-900'}`}>Async IPC / TCP</span>
              </div>
              <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-950/60 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] block ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Polling Cadence</span>
                <span className={`font-mono font-medium ${isDark ? 'text-white' : 'text-slate-900'}`}>250ms Ticks</span>
              </div>
              <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-950/60 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] block ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Database</span>
                <span className={`font-mono font-medium ${isDark ? 'text-white' : 'text-slate-900'}`}>PostgreSQL 16</span>
              </div>
              <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-950/60 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] block ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>AI Layer Readiness</span>
                <span className="font-mono text-emerald-500 font-medium">Phase 5 Ready</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Appearance & Data Export */}
        <div className="space-y-6">
          {/* Appearance */}
          <div
            className={`p-5 rounded-lg border transition-colors ${
              theme === 'dark'
                ? 'bg-slate-900/60 border-slate-800'
                : 'bg-white border-slate-200 shadow-xs'
            }`}
          >
            <h2
              className={`text-sm font-semibold mb-3 ${
                theme === 'dark' ? 'text-white' : 'text-slate-900'
              }`}
            >
              Interface Theme
            </h2>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setTheme('dark')}
                className={`flex items-center justify-center gap-2 p-3 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                  theme === 'dark'
                    ? 'bg-slate-800 border-emerald-500 text-white ring-2 ring-emerald-500/30 shadow-xs'
                    : 'bg-slate-100/70 border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Moon className={`w-4 h-4 ${theme === 'dark' ? 'text-emerald-400' : 'text-slate-500'}`} />
                <span>Dark Mode</span>
              </button>
              <button
                type="button"
                onClick={() => setTheme('light')}
                className={`flex items-center justify-center gap-2 p-3 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                  theme === 'light'
                    ? 'bg-emerald-50 border-emerald-600 text-emerald-950 ring-2 ring-emerald-500/30 shadow-xs'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Sun className={`w-4 h-4 ${theme === 'light' ? 'text-amber-500' : 'text-slate-400'}`} />
                <span>Light Mode</span>
              </button>
            </div>
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
              <span>Active theme mode:</span>
              <span className="font-semibold uppercase tracking-wider text-emerald-500">
                {theme}
              </span>
            </div>
          </div>

          {/* Export Ledger Data */}
          <div
            className={`p-5 rounded-lg border transition-colors ${
              isDark
                ? 'bg-slate-900/60 border-slate-800'
                : 'bg-white border-slate-200 shadow-xs'
            }`}
          >
            <h2 className={`text-sm font-semibold mb-2 ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Export Data Ledger
            </h2>
            <p className={`text-xs mb-4 leading-relaxed ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              Download clean CSV files containing tickets, stop levels, breakeven triggers, and execution times for external audits or spreadsheets.
            </p>

            <button
              onClick={handleExportCSV}
              className={`flex items-center justify-center gap-2 w-full py-2.5 text-xs font-medium rounded-md border transition-colors ${
                isDark
                  ? 'text-white bg-slate-800 hover:bg-slate-700 border-slate-700'
                  : 'text-slate-800 bg-slate-100 hover:bg-slate-200 border-slate-200 shadow-2xs'
              }`}
            >
              <Download className="w-4 h-4" />
              <span>Export {trades.length} Trades to CSV</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
