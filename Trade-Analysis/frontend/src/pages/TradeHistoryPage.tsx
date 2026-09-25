import React, { useState, useMemo } from 'react';
import { useTrading } from '../context/TradingContext';
import {
  Search,
  Filter,
  ArrowUpDown,
  Download,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Layers,
} from 'lucide-react';
import { Trade, RiskFreeStatus } from '../types/trading';

export const TradeHistoryPage: React.FC = () => {
  const { trades, setSelectedTradeForDetails, isAllAccounts, activeAccount, theme } = useTrading();
  const isDark = theme === 'dark';

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('ALL');
  const [selectedSide, setSelectedSide] = useState<string>('ALL');
  const [selectedOutcome, setSelectedOutcome] = useState<string>('ALL');
  const [selectedRiskFree, setSelectedRiskFree] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'date' | 'pl'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Extract unique symbols from current isolated trades
  const uniqueSymbols = useMemo(() => {
    return Array.from(new Set(trades.map((t) => t.symbol))).sort();
  }, [trades]);

  // Filtering & Sorting
  const filteredTrades = useMemo(() => {
    return trades
      .filter((trade) => {
        // Search
        if (searchTerm) {
          const term = searchTerm.toLowerCase();
          const matchTicket = trade.ticket.toString().includes(term);
          const matchSymbol = trade.symbol.toLowerCase().includes(term);
          const matchStrat = trade.strategy_name.toLowerCase().includes(term);
          if (!matchTicket && !matchSymbol && !matchStrat) return false;
        }

        // Symbol filter
        if (selectedSymbol !== 'ALL' && trade.symbol !== selectedSymbol) return false;

        // Side filter
        if (selectedSide !== 'ALL' && trade.direction !== selectedSide) return false;

        // Outcome filter
        if (selectedOutcome !== 'ALL' && trade.status !== selectedOutcome) return false;

        // Risk-Free filter
        if (selectedRiskFree !== 'ALL' && trade.risk_free_status !== selectedRiskFree) return false;

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'pl') {
          return sortOrder === 'desc' ? b.net_pl - a.net_pl : a.net_pl - b.net_pl;
        } else {
          return sortOrder === 'desc'
            ? new Date(b.entry_time).getTime() - new Date(a.entry_time).getTime()
            : new Date(a.entry_time).getTime() - new Date(b.entry_time).getTime();
        }
      });
  }, [trades, searchTerm, selectedSymbol, selectedSide, selectedOutcome, selectedRiskFree, sortBy, sortOrder]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredTrades.length / itemsPerPage));
  const paginatedTrades = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredTrades.slice(start, start + itemsPerPage);
  }, [filteredTrades, currentPage, itemsPerPage]);

  const toggleSort = (field: 'date' | 'pl') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-200">
      {/* Header */}
      <div
        className={`flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b ${
          isDark ? 'border-slate-800/80' : 'border-slate-200'
        }`}
      >
        <div>
          <div className="flex items-center gap-3">
            <h1 className={`text-xl sm:text-2xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Trade History
            </h1>
            <span
              className={`text-xs font-mono px-2 py-0.5 rounded border ${
                isDark
                  ? 'text-slate-400 bg-slate-900 border-slate-800'
                  : 'text-slate-600 bg-slate-100 border-slate-200'
              }`}
            >
              {filteredTrades.length} trades recorded
            </span>
          </div>
          <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Complete execution ledger with risk-management parameters, breakeven triggers, and audit logs
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
              <span>All Accounts Combined</span>
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

      {/* Filters and Search Bar */}
      <div
        className={`p-4 rounded-lg border space-y-3 transition-colors ${
          isDark
            ? 'bg-slate-900/60 border-slate-800'
            : 'bg-white border-slate-200 shadow-xs'
        }`}
      >
        <div className="flex flex-col sm:flex-row items-center gap-3">
          {/* Search Box */}
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by symbol, ticket #, or strategy..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className={`w-full pl-9 pr-4 py-2 text-xs rounded-md border focus:outline-hidden transition-colors ${
                isDark
                  ? 'bg-slate-950/80 border-slate-700/80 text-white placeholder-slate-500 focus:border-emerald-500'
                  : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:border-emerald-600 focus:bg-white'
              }`}
            />
          </div>

          {/* Quick Sort Buttons */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={() => toggleSort('date')}
              className={`flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-md border transition-colors ${
                sortBy === 'date'
                  ? isDark
                    ? 'bg-slate-800 text-white border-slate-600'
                    : 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                  : isDark
                  ? 'text-slate-400 border-slate-800 hover:text-white'
                  : 'text-slate-600 border-slate-200 hover:text-slate-900 bg-white'
              }`}
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
              <span>Date ({sortBy === 'date' ? sortOrder.toUpperCase() : 'Sort'})</span>
            </button>
            <button
              onClick={() => toggleSort('pl')}
              className={`flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-md border transition-colors ${
                sortBy === 'pl'
                  ? isDark
                    ? 'bg-slate-800 text-white border-slate-600'
                    : 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                  : isDark
                  ? 'text-slate-400 border-slate-800 hover:text-white'
                  : 'text-slate-600 border-slate-200 hover:text-slate-900 bg-white'
              }`}
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
              <span>P&L ({sortBy === 'pl' ? sortOrder.toUpperCase() : 'Sort'})</span>
            </button>
          </div>
        </div>

        {/* Filter Dropdowns */}
        <div
          className={`flex flex-wrap items-center gap-2 pt-2 border-t text-xs ${
            isDark ? 'border-slate-800/60' : 'border-slate-100'
          }`}
        >
          {/* Symbol */}
          <div className="flex items-center gap-1.5">
            <span className={`text-[11px] uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Symbol:</span>
            <select
              value={selectedSymbol}
              onChange={(e) => {
                setSelectedSymbol(e.target.value);
                setCurrentPage(1);
              }}
              className={`px-2 py-1 rounded border text-xs focus:outline-hidden ${
                isDark
                  ? 'bg-slate-950 border-slate-800 text-slate-300'
                  : 'bg-white border-slate-200 text-slate-700'
              }`}
            >
              <option value="ALL">All Symbols</option>
              {uniqueSymbols.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Side */}
          <div className="flex items-center gap-1.5">
            <span className={`text-[11px] uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Side:</span>
            <select
              value={selectedSide}
              onChange={(e) => {
                setSelectedSide(e.target.value);
                setCurrentPage(1);
              }}
              className={`px-2 py-1 rounded border text-xs focus:outline-hidden ${
                isDark
                  ? 'bg-slate-950 border-slate-800 text-slate-300'
                  : 'bg-white border-slate-200 text-slate-700'
              }`}
            >
              <option value="ALL">All Sides</option>
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>

          {/* Result */}
          <div className="flex items-center gap-1.5">
            <span className={`text-[11px] uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Result:</span>
            <select
              value={selectedOutcome}
              onChange={(e) => {
                setSelectedOutcome(e.target.value);
                setCurrentPage(1);
              }}
              className={`px-2 py-1 rounded border text-xs focus:outline-hidden ${
                isDark
                  ? 'bg-slate-950 border-slate-800 text-slate-300'
                  : 'bg-white border-slate-200 text-slate-700'
              }`}
            >
              <option value="ALL">All Results</option>
              <option value="WIN">WIN</option>
              <option value="LOSS">LOSS</option>
              <option value="BREAKEVEN">BREAKEVEN</option>
            </select>
          </div>

          {/* Risk-Free Status Filter (Requirement #3) */}
          <div className="flex items-center gap-1.5">
            <span className={`text-[11px] uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Risk-Free:</span>
            <select
              value={selectedRiskFree}
              onChange={(e) => {
                setSelectedRiskFree(e.target.value);
                setCurrentPage(1);
              }}
              className={`px-2 py-1 rounded border text-xs focus:outline-hidden ${
                isDark
                  ? 'bg-slate-950 border-slate-800 text-slate-300'
                  : 'bg-white border-slate-200 text-slate-700'
              }`}
            >
              <option value="ALL">All Statuses</option>
              <option value="YES">Risk-Free: YES</option>
              <option value="NO">Risk-Free: NO</option>
              <option value="N/A">Not Applicable</option>
            </select>
          </div>
        </div>
      </div>

      {/* Trades Table */}
      <div
        className={`rounded-lg border overflow-hidden transition-colors ${
          isDark
            ? 'bg-slate-900/60 border-slate-800'
            : 'bg-white border-slate-200 shadow-xs'
        }`}
      >
        {paginatedTrades.length === 0 ? (
          <div className="py-16 text-center text-xs">
            <p className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>No trades match your search or filter</p>
            <p className={`mt-1 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Try clearing filters or switching accounts.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs min-w-[850px]">
              <thead
                className={`border-b text-[11px] uppercase tracking-wider ${
                  isDark
                    ? 'border-slate-800 bg-slate-950/70 text-slate-400'
                    : 'border-slate-200 bg-slate-100 text-slate-600'
                }`}
              >
                <tr>
                  <th className="py-3 px-4">Time</th>
                  <th className="py-3 px-4">Symbol</th>
                  <th className="py-3 px-4">Side</th>
                  <th className="py-3 px-4">Entry / Exit</th>
                  <th className="py-3 px-4">Lot</th>
                  <th className="py-3 px-4">SL / TP</th>
                  {/* Risk Management Columns (Requirement #3) */}
                  <th className="py-3 px-4">Initial Risk</th>
                  <th className="py-3 px-4">Risk-Free</th>
                  <th className="py-3 px-4">BE Price</th>
                  <th className="py-3 px-4">Strategy</th>
                  <th className="py-3 px-4 text-right">Final P&L</th>
                </tr>
              </thead>
              <tbody
                className={`divide-y ${
                  isDark ? 'divide-slate-800/60 text-slate-300' : 'divide-slate-200 text-slate-700'
                }`}
              >
                {paginatedTrades.map((trade: Trade) => {
                  const isPositive = trade.net_pl > 0;
                  const isLoss = trade.net_pl < 0;

                  return (
                    <tr
                      key={trade.id}
                      onClick={() => setSelectedTradeForDetails(trade)}
                      className={`transition-colors cursor-pointer group text-xs ${
                        isDark ? 'hover:bg-slate-800/40' : 'hover:bg-slate-50'
                      }`}
                    >
                      <td className={`py-3 px-4 font-mono text-[11px] whitespace-nowrap ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        {trade.entry_time.slice(11, 16)}
                        <span className={`block text-[10px] ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
                          {trade.entry_time.slice(0, 10)}
                        </span>
                      </td>

                      <td className={`py-3 px-4 font-bold font-sans ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        {trade.symbol}
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`font-semibold px-2 py-0.5 rounded text-[10px] font-sans ${
                            trade.direction === 'BUY'
                              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                              : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30'
                          }`}
                        >
                          {trade.direction}
                        </span>
                      </td>

                      <td className={`py-3 px-4 font-mono tabular-nums text-[11px] ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                        <div>{trade.entry_price.toFixed(5)}</div>
                        <div className={isDark ? 'text-slate-500' : 'text-slate-400'}>{trade.exit_price.toFixed(5)}</div>
                      </td>

                      <td className={`py-3 px-4 font-mono tabular-nums ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                        {trade.volume.toFixed(2)}
                      </td>

                      <td className={`py-3 px-4 font-mono text-[11px] tabular-nums ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        <span className="text-rose-500">{trade.stop_loss ? trade.stop_loss.toFixed(5) : '—'}</span>
                        {' / '}
                        <span className="text-emerald-500">{trade.take_profit ? trade.take_profit.toFixed(5) : '—'}</span>
                      </td>

                      {/* Initial Risk % and Amount (Requirement #3) */}
                      <td className={`py-3 px-4 font-mono tabular-nums ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                        <div>{trade.initial_risk_percent}%</div>
                        <div className={`text-[10px] ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                          ${trade.initial_risk_amount.toFixed(2)}
                        </div>
                      </td>

                      {/* Risk-Free Status Badge (Requirement #3) */}
                      <td className="py-3 px-4 font-sans">
                        <span
                          className={`text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wider inline-flex items-center gap-1 ${
                            trade.risk_free_status === 'YES'
                              ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30'
                              : trade.risk_free_status === 'NO'
                              ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20'
                              : isDark
                              ? 'bg-slate-800 text-slate-500'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          {trade.risk_free_status === 'YES' && (
                            <ShieldCheck className="w-3 h-3 text-emerald-500" />
                          )}
                          Risk-Free: {trade.risk_free_status}
                        </span>
                      </td>

                      {/* Break-Even Price (Requirement #3) */}
                      <td className={`py-3 px-4 font-mono text-[11px] tabular-nums ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        {trade.break_even_price ? trade.break_even_price.toFixed(5) : '—'}
                      </td>

                      <td className={`py-3 px-4 font-sans text-[11px] truncate max-w-[120px] ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                        {trade.strategy_name}
                      </td>

                      {/* Final P&L (Requirement #2 clean font & #3) */}
                      <td className="py-3 px-4 text-right font-sans font-semibold tabular-nums text-sm">
                        <span
                          className={
                            isPositive
                              ? 'text-emerald-500'
                              : isLoss
                              ? 'text-rose-500'
                              : isDark ? 'text-slate-400' : 'text-slate-500'
                          }
                        >
                          {isPositive ? '+' : ''}${trade.net_pl.toFixed(2)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div
          className={`flex items-center justify-between px-4 py-3 border-t text-xs ${
            isDark
              ? 'border-slate-800 bg-slate-950/60 text-slate-400'
              : 'border-slate-200 bg-slate-50 text-slate-600'
          }`}
        >
          <span>
            Showing{' '}
            <strong className={isDark ? 'text-white' : 'text-slate-900'}>
              {filteredTrades.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0}
            </strong>{' '}
            to{' '}
            <strong className={isDark ? 'text-white' : 'text-slate-900'}>
              {Math.min(currentPage * itemsPerPage, filteredTrades.length)}
            </strong>{' '}
            of <strong className={isDark ? 'text-white' : 'text-slate-900'}>{filteredTrades.length}</strong> trades
          </span>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className={`p-1 rounded transition-colors disabled:opacity-40 ${
                isDark
                  ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 shadow-2xs'
              }`}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className={`px-2 font-mono tabular-nums ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className={`p-1 rounded transition-colors disabled:opacity-40 ${
                isDark
                  ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 shadow-2xs'
              }`}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
