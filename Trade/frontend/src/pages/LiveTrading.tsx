import { MetricCard } from '@/components/ui/MetricCard';
import { Badge } from '@/components/ui/Badge';
import { StatusDot } from '@/components/ui/StatusDot';
import { EmptyState } from '@/components/ui/EmptyState';
import { useAccount } from '@/hooks/useAccount';
import { mockDashboardMetrics, mockPositions } from '@/services/mockData';
import {
  formatCurrency,
  formatPrice,
  getPnlClass,
  formatTime,
  cn,
} from '@/utils/format';
import {
  Wifi,
  WifiOff,
  Wallet,
  DollarSign,
  ShieldCheck,
  ArrowDownUp,
  TrendingDown,
  Activity,
} from 'lucide-react';

export default function LiveTrading() {
  const { selectedAccount, isAllAccounts, dataMode } = useAccount();
  const metrics = mockDashboardMetrics;
  const isConnected = selectedAccount?.status === 'connected';
  const positions = mockPositions;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Live Trading</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            {isAllAccounts ? 'All Accounts' : selectedAccount?.accountName} · {positions.length} open position{positions.length !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Connection Status */}
        <div className="flex items-center gap-3">
          <div className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg border',
            isConnected
              ? 'bg-profit/5 border-profit/20'
              : 'bg-loss/5 border-loss/20'
          )}>
            {isConnected ? <Wifi size={16} className="text-profit" /> : <WifiOff size={16} className="text-loss" />}
            <div>
              <p className="text-sm font-medium text-text-primary">
                MT5 {isConnected ? 'Connected' : 'Disconnected'}
              </p>
              {selectedAccount?.lastSync && (
                <p className="text-[11px] text-text-muted">
                  Last sync: {new Date(selectedAccount.lastSync).toLocaleTimeString()}
                </p>
              )}
            </div>
            <StatusDot status={isConnected ? 'online' : 'offline'} />
          </div>
        </div>
      </div>

      {/* Demo Banner */}
      {dataMode === 'demo' && (
        <div className="px-3 py-2 rounded-lg bg-warning/5 border border-warning/10">
          <p className="text-xs text-warning">
            <span className="font-semibold">Demo Mode</span> — Displaying sample positions. Not real trading data.
          </p>
        </div>
      )}

      {/* Account Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <MetricCard
          label="Balance"
          value={formatCurrency(metrics.account.balance).replace('+', '')}
          icon={<Wallet size={18} />}
        />
        <MetricCard
          label="Equity"
          value={formatCurrency(metrics.account.equity).replace('+', '')}
          icon={<DollarSign size={18} />}
        />
        <MetricCard
          label="Margin"
          value={formatCurrency(metrics.account.margin).replace('+', '')}
          icon={<ShieldCheck size={18} />}
        />
        <MetricCard
          label="Free Margin"
          value={formatCurrency(metrics.account.freeMargin).replace('+', '')}
          icon={<ArrowDownUp size={18} />}
        />
        <MetricCard
          label="Drawdown"
          value={`${metrics.today.drawdown.toFixed(1)}%`}
          icon={<TrendingDown size={18} />}
        />
      </div>

      {/* Open Positions */}
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
          Open Positions
        </h2>

        {positions.length === 0 ? (
          <EmptyState
            icon={<Activity size={40} />}
            title="No open positions"
            description="There are currently no open trades. Positions will appear here when trades are opened."
          />
        ) : (
          <div className="card !p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {['Symbol', 'Direction', 'Volume', 'Entry', 'Current', 'SL', 'TP', 'Floating P&L', 'Duration'].map((h) => (
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
                  {positions.map((pos) => (
                    <tr
                      key={pos.id}
                      className="border-b border-border/50 last:border-0 hover:bg-surface-overlay transition-colors"
                    >
                      <td className="px-4 py-3 font-medium text-text-primary">{pos.symbol}</td>
                      <td className="px-4 py-3">
                        <Badge variant={pos.direction === 'BUY' ? 'success' : 'danger'} size="sm">
                          {pos.direction}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-text-secondary">{pos.volume.toFixed(2)}</td>
                      <td className="px-4 py-3 text-text-secondary font-mono text-xs">
                        {formatPrice(pos.entryPrice)}
                      </td>
                      <td className="px-4 py-3 text-text-primary font-mono text-xs font-medium">
                        {formatPrice(pos.currentPrice)}
                      </td>
                      <td className="px-4 py-3 text-text-muted font-mono text-xs">
                        {formatPrice(pos.stopLoss)}
                      </td>
                      <td className="px-4 py-3 text-text-muted font-mono text-xs">
                        {formatPrice(pos.takeProfit)}
                      </td>
                      <td className={cn('px-4 py-3 font-semibold', getPnlClass(pos.floatingPL))}>
                        {formatCurrency(pos.floatingPL)}
                      </td>
                      <td className="px-4 py-3 text-text-muted text-xs">{pos.duration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Market Status */}
      <div className="card">
        <h3 className="text-sm font-medium text-text-primary mb-3">System Status</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Trading System', status: 'online' as const },
            { label: 'Market Data', status: 'online' as const },
            { label: 'Strategy Engine', status: 'online' as const },
            { label: 'Risk Engine', status: 'online' as const },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <StatusDot status={item.status} size="sm" />
              <span className="text-xs text-text-secondary">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
