import { useState, useMemo } from 'react';
import type { Trade, TradeDirection, TradeResult } from '@/types';
import { TradeDetail } from '@/components/trades/TradeDetail';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { mockTrades } from '@/services/mockData';
import { useAccount } from '@/hooks/useAccount';
import {
  formatCurrency,
  formatPrice,
  formatTime,
  getPnlClass,
  formatPercent,
  cn,
} from '@/utils/format';
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  History,
  Shield,
} from 'lucide-react';

const PAGE_SIZE = 10;

export default function TradeHistory() {
  const { selectedAccountId, isAllAccounts } = useAccount();
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
  const [search, setSearch] = useState('');
  const [directionFilter, setDirectionFilter] = useState<TradeDirection | ''>('');
  const [resultFilter, setResultFilter] = useState<TradeResult | ''>('');
  const [strategyFilter, setStrategyFilter] = useState('');
  const [page, setPage] = useState(1);

  const filteredTrades = useMemo(() => {
    let result = mockTrades;

    // Account filter
    if (!isAllAccounts && selectedAccountId) {
      result = result.filter((t) => t.accountId === selectedAccountId);
    }

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (t) =>
          t.symbol.toLowerCase().includes(q) ||
          t.id.toLowerCase().includes(q)
      );
    }

    if (directionFilter) {
      result = result.filter((t) => t.direction === directionFilter);
    }

    if (resultFilter) {
      result = result.filter((t) => t.result === resultFilter);
    }

    if (strategyFilter) {
      result = result.filter((t) => t.strategyName === strategyFilter);
    }

    return result;
  }, [search, directionFilter, resultFilter, strategyFilter, selectedAccountId, isAllAccounts]);

  const totalPages = Math.max(1, Math.ceil(filteredTrades.length / PAGE_SIZE));
  const paginatedTrades = filteredTrades.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const strategies = [...new Set(mockTrades.map((t) => t.strategyName).filter(Boolean))];

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Trade History</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            {filteredTrades.length} trades · {isAllAccounts ? 'All Accounts' : 'Selected Account'}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Search by symbol or trade ID..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 pr-3 py-2 text-sm bg-surface-raised border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors"
          />
        </div>

        <select
          value={directionFilter}
          onChange={(e) => { setDirectionFilter(e.target.value as TradeDirection | ''); setPage(1); }}
          className="px-3 py-2 text-sm bg-surface-raised border border-border rounded-lg text-text-primary focus:outline-none focus:border-accent"
        >
          <option value="">All Sides</option>
          <option value="BUY">BUY</option>
          <option value="SELL">SELL</option>
        </select>

        <select
          value={resultFilter ?? ''}
          onChange={(e) => { setResultFilter((e.target.value as TradeResult) || ''); setPage(1); }}
          className="px-3 py-2 text-sm bg-surface-raised border border-border rounded-lg text-text-primary focus:outline-none focus:border-accent"
        >
          <option value="">All Results</option>
          <option value="WIN">WIN</option>
          <option value="LOSS">LOSS</option>
          <option value="BREAKEVEN">BREAKEVEN</option>
        </select>

        <select
          value={strategyFilter}
          onChange={(e) => { setStrategyFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 text-sm bg-surface-raised border border-border rounded-lg text-text-primary focus:outline-none focus:border-accent"
        >
          <option value="">All Strategies</option>
          {strategies.map((s) => (
            <option key={s} value={s!}>{s}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      {paginatedTrades.length === 0 ? (
        <EmptyState
          icon={<History size={40} />}
          title="No trades found"
          description="Adjust your filters or connect MT5 to start receiving trades."
        />
      ) : (
        <div className="card !p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {['Time', 'Symbol', 'Side', 'Entry', 'Exit', 'Lot', 'SL', 'TP', 'Risk', 'Risk-Free', 'P&L', 'Status', 'Strategy'].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paginatedTrades.map((trade) => (
                  <tr
                    key={trade.id}
                    onClick={() => setSelectedTrade(trade)}
                    className="border-b border-border/50 last:border-0 hover:bg-surface-overlay cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 text-text-secondary whitespace-nowrap">
                      {formatTime(trade.entryTime)}
                    </td>
                    <td className="px-4 py-3 font-medium text-text-primary whitespace-nowrap">
                      {trade.symbol}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={trade.direction === 'BUY' ? 'success' : 'danger'} size="sm">
                        {trade.direction}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-text-secondary font-mono text-xs whitespace-nowrap">
                      {formatPrice(trade.entryPrice)}
                    </td>
                    <td className="px-4 py-3 text-text-secondary font-mono text-xs whitespace-nowrap">
                      {formatPrice(trade.exitPrice)}
                    </td>
                    <td className="px-4 py-3 text-text-secondary whitespace-nowrap">
                      {trade.volume.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-text-muted font-mono text-xs whitespace-nowrap">
                      {formatPrice(trade.stopLoss)}
                    </td>
                    <td className="px-4 py-3 text-text-muted font-mono text-xs whitespace-nowrap">
                      {formatPrice(trade.takeProfit)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {trade.initialRiskPercent !== null ? (
                        <span className="text-xs text-text-secondary">
                          {formatPercent(trade.initialRiskPercent)}
                        </span>
                      ) : (
                        <span className="text-xs text-text-muted">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Badge
                        variant={
                          trade.riskFreeStatus === 'YES'
                            ? 'success'
                            : trade.riskFreeStatus === 'NO'
                            ? 'danger'
                            : 'neutral'
                        }
                        size="sm"
                      >
                        <Shield size={9} className="mr-0.5" />
                        {trade.riskFreeStatus}
                      </Badge>
                    </td>
                    <td className={cn('px-4 py-3 font-semibold whitespace-nowrap', getPnlClass(trade.profitLoss ?? 0))}>
                      {trade.profitLoss !== null ? formatCurrency(trade.profitLoss) : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={
                          trade.result === 'WIN' ? 'success' : trade.result === 'LOSS' ? 'danger' : 'neutral'
                        }
                        size="sm"
                      >
                        {trade.result ?? trade.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-text-muted text-xs whitespace-nowrap">
                      {trade.strategyName ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-border">
              <span className="text-xs text-text-muted">
                Page {page} of {totalPages}
              </span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded hover:bg-surface-overlay text-text-muted disabled:opacity-30 transition-colors"
                >
                  <ChevronLeft size={16} />
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="p-1.5 rounded hover:bg-surface-overlay text-text-muted disabled:opacity-30 transition-colors"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Trade Detail Panel */}
      {selectedTrade && (
        <TradeDetail trade={selectedTrade} onClose={() => setSelectedTrade(null)} />
      )}
    </div>
  );
}
