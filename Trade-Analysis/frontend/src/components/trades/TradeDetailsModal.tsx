import React from 'react';
import { X, ShieldCheck, ShieldAlert, Cpu, Sparkles, Clock, CheckCircle2, TrendingUp, TrendingDown } from 'lucide-react';
import { Trade } from '../../types/trading';
import { useTrading } from '../../context/TradingContext';

interface TradeDetailsModalProps {
  trade: Trade | null;
  onClose: () => void;
}

export const TradeDetailsModal: React.FC<TradeDetailsModalProps> = ({ trade, onClose }) => {
  const { theme } = useTrading();
  const isDark = theme === 'dark';

  if (!trade) return null;

  const isWin = trade.status === 'WIN';
  const isLoss = trade.status === 'LOSS';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/70 backdrop-blur-xs animate-in fade-in-50 duration-150">
      <div
        className={`w-full max-w-xl rounded-xl border shadow-2xl overflow-hidden transition-colors ${
          isDark
            ? 'border-slate-800 bg-[#0d131f] text-slate-200'
            : 'border-slate-200 bg-white text-slate-800'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className={`flex items-center justify-between px-5 sm:px-6 py-4 border-b ${
            isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-slate-50'
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`p-2 rounded-lg border ${
                isWin
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-500'
                  : isLoss
                  ? 'bg-rose-500/10 border-rose-500/30 text-rose-500'
                  : isDark
                  ? 'bg-slate-800 border-slate-700 text-slate-300'
                  : 'bg-slate-100 border-slate-200 text-slate-600'
              }`}
            >
              {trade.direction === 'BUY' ? (
                <TrendingUp className="w-5 h-5" />
              ) : (
                <TrendingDown className="w-5 h-5" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className={`text-base font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  Trade #{trade.ticket}
                </h3>
                <span
                  className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
                    isDark
                      ? 'text-slate-300 bg-slate-800 border-slate-700'
                      : 'text-slate-700 bg-slate-100 border-slate-200'
                  }`}
                >
                  {trade.symbol}
                </span>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    trade.direction === 'BUY'
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                      : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30'
                  }`}
                >
                  {trade.direction}
                </span>
              </div>
              <span className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Status: CLOSED</span>
            </div>
          </div>

          <button
            onClick={onClose}
            className={`p-1.5 rounded-lg transition-colors ${
              isDark
                ? 'text-slate-400 hover:text-white hover:bg-slate-800'
                : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
            }`}
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-4 sm:p-6 space-y-4 sm:space-y-5 max-h-[80vh] overflow-y-auto">
          {/* Key Metric Highlights */}
          <div
            className={`grid grid-cols-3 gap-3 p-3.5 rounded-lg border ${
              isDark
                ? 'bg-slate-900/80 border-slate-800'
                : 'bg-slate-50 border-slate-200'
            }`}
          >
            <div>
              <span className={`text-[11px] block mb-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Net P&L</span>
              <span
                className={`text-xl font-semibold font-sans tabular-nums ${
                  trade.net_pl >= 0 ? 'text-emerald-500' : 'text-rose-500'
                }`}
              >
                {trade.net_pl >= 0 ? '+' : ''}${trade.net_pl.toFixed(2)}
              </span>
            </div>
            <div>
              <span className={`text-[11px] block mb-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Result</span>
              <span
                className={`text-xs font-semibold uppercase px-2 py-0.5 rounded inline-block ${
                  isWin
                    ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300'
                    : isLoss
                    ? 'bg-rose-500/20 text-rose-700 dark:text-rose-300'
                    : isDark
                    ? 'bg-slate-800 text-slate-300'
                    : 'bg-slate-200 text-slate-700'
                }`}
              >
                {trade.status}
              </span>
            </div>
            <div>
              <span className={`text-[11px] block mb-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Risk : Reward</span>
              <span className={`text-sm font-semibold font-mono tabular-nums ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                1 : {trade.risk_reward_ratio?.toFixed(2) || '1.50'}
              </span>
            </div>
          </div>

          {/* Execution Prices & Volumes */}
          <div className="space-y-2">
            <h4 className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
              Execution Details
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-900/50 border-slate-800/80' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Entry Price</span>
                <span className={`text-xs font-mono font-medium tabular-nums ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  {trade.entry_price.toFixed(5)}
                </span>
              </div>
              <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-900/50 border-slate-800/80' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Exit Price</span>
                <span className={`text-xs font-mono font-medium tabular-nums ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  {trade.exit_price.toFixed(5)}
                </span>
              </div>
              <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-900/50 border-slate-800/80' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Stop Loss</span>
                <span className="text-xs font-mono font-medium text-rose-500 tabular-nums">
                  {trade.stop_loss ? trade.stop_loss.toFixed(5) : 'None'}
                </span>
              </div>
              <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-900/50 border-slate-800/80' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Take Profit</span>
                <span className="text-xs font-mono font-medium text-emerald-500 tabular-nums">
                  {trade.take_profit ? trade.take_profit.toFixed(5) : 'None'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5 pt-1">
              <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-900/50 border-slate-800/80' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Lot Size (Volume)</span>
                <span className={`text-xs font-mono font-medium ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                  {trade.volume.toFixed(2)} Lots
                </span>
              </div>
              <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-900/50 border-slate-800/80' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Commission & Swap</span>
                <span className={`text-xs font-mono font-medium ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                  ${(trade.commission + trade.swap).toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* Risk Management & Risk-Free Details (Requirement #3) */}
          <div className="space-y-2">
            <h4 className={`text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              Risk Management Parameters
            </h4>
            <div className={`p-3.5 rounded-lg border space-y-2.5 ${isDark ? 'bg-slate-900/50 border-slate-800/80' : 'bg-slate-50 border-slate-200'}`}>
              <div className="flex items-center justify-between text-xs">
                <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Risk-Free Status:</span>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    trade.risk_free_status === 'YES'
                      ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30'
                      : trade.risk_free_status === 'NO'
                      ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-500/30'
                      : isDark
                      ? 'bg-slate-800 text-slate-400'
                      : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  Risk-Free: {trade.risk_free_status}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Initial Risk:</span>
                <span className={`font-mono tabular-nums ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                  {trade.initial_risk_percent}% (${trade.initial_risk_amount.toFixed(2)})
                </span>
              </div>

              {trade.break_even_price && (
                <div className="flex items-center justify-between text-xs">
                  <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Break-Even Price:</span>
                  <span className="font-mono font-medium text-emerald-500 tabular-nums">
                    {trade.break_even_price.toFixed(5)}
                  </span>
                </div>
              )}

              {trade.risk_free_activated_time && (
                <div className="flex items-center justify-between text-xs">
                  <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Risk-Free Activated:</span>
                  <span className={`font-mono tabular-nums ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                    {trade.risk_free_activated_time}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Timestamps & Strategy */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-900/50 border-slate-800/80' : 'bg-slate-50 border-slate-200'}`}>
              <span className={`text-[10px] block mb-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Entry Time</span>
              <span className={`font-mono ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{trade.entry_time}</span>
            </div>
            <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-900/50 border-slate-800/80' : 'bg-slate-50 border-slate-200'}`}>
              <span className={`text-[10px] block mb-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Exit Time</span>
              <span className={`font-mono ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{trade.exit_time}</span>
            </div>
          </div>

          <div className={`p-3 rounded-lg border flex items-center justify-between text-xs ${isDark ? 'bg-slate-900/50 border-slate-800/80' : 'bg-slate-50 border-slate-200'}`}>
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-emerald-500" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Strategy Version:</span>
            </div>
            <span className={`font-medium ${isDark ? 'text-white' : 'text-slate-900'}`}>{trade.strategy_name}</span>
          </div>

          {/* Reserved AI Analysis Section (Requirement #11 & #13) */}
          <div className={`p-4 rounded-lg border ${isDark ? 'border-slate-800 bg-slate-900/30' : 'border-slate-200 bg-slate-50'}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-slate-400" />
                <h4 className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                  AI Trade Analysis
                </h4>
              </div>
              <span
                className={`text-[11px] font-medium px-2 py-0.5 rounded border ${
                  isDark
                    ? 'text-slate-400 bg-slate-800 border-slate-700'
                    : 'text-slate-600 bg-slate-200 border-slate-300'
                }`}
              >
                Coming soon
              </span>
            </div>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
              Automated cognitive analysis of entry timing, liquidity draw, and slippage deviation will be activated in Phase 5.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className={`flex items-center justify-end px-6 py-3 border-t ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-slate-50'}`}>
          <button
            onClick={onClose}
            className={`px-4 py-1.5 text-xs font-medium rounded-md transition-colors ${
              isDark
                ? 'text-white bg-slate-800 hover:bg-slate-700'
                : 'text-slate-800 bg-slate-200 hover:bg-slate-300'
            }`}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
