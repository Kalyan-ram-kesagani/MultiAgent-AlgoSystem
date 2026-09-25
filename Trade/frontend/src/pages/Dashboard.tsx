import { MetricCard } from '@/components/ui/MetricCard';
import { EquityCurve } from '@/charts/EquityCurve';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { SystemHealth } from '@/components/dashboard/SystemHealth';
import { RiskStatusCard } from '@/components/dashboard/RiskStatus';
import { StatusDot } from '@/components/ui/StatusDot';
import { useAccount } from '@/hooks/useAccount';
import {
  mockDashboardMetrics,
  mockEquityCurve,
  mockActivities,
  mockSystemHealth,
  mockRiskStatus,
} from '@/services/mockData';
import {
  formatCurrency,
  formatPercent,
  getPnlClass,
  getGreeting,
  formatDate,
  getMarketSession,
} from '@/utils/format';
import {
  TrendingUp,
  BarChart2,
  Target,
  TrendingDown,
  Wallet,
  DollarSign,
  ArrowDownUp,
  Hash,
  Percent,
  Award,
} from 'lucide-react';

export default function Dashboard() {
  const { selectedAccount, isAllAccounts, dataMode } = useAccount();
  const metrics = mockDashboardMetrics;
  const isConnected = selectedAccount?.status === 'connected';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h1 className="text-xl font-semibold text-text-primary">{getGreeting()}</h1>
            <p className="text-sm text-text-secondary mt-0.5">
              {formatDate(new Date().toISOString())} · {getMarketSession()}
            </p>
          </div>
          <div className="flex items-center gap-4">
            {/* Account context */}
            <div className="text-right hidden sm:block">
              <p className="text-xs text-text-muted">
                {isAllAccounts ? 'All Accounts' : selectedAccount?.accountName}
              </p>
              {!isAllAccounts && selectedAccount && (
                <p className="text-[11px] text-text-muted">
                  MT5 {selectedAccount.maskedNumber}
                </p>
              )}
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface-raised border border-border">
              <StatusDot status={isConnected ? 'online' : 'offline'} size="sm" />
              <span className="text-xs text-text-secondary">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>

        {/* Demo mode info banner */}
        {dataMode === 'demo' && (
          <div className="mt-3 px-3 py-2 rounded-lg bg-warning/5 border border-warning/10">
            <p className="text-xs text-warning">
              <span className="font-semibold">Demo Mode</span> — Sample data for UI preview. Not real trading results.
            </p>
          </div>
        )}
      </div>

      {/* Today's Metrics */}
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Today</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard
            label="P&L"
            value={formatCurrency(metrics.today.pnl)}
            valueClass={getPnlClass(metrics.today.pnl)}
            icon={<TrendingUp size={18} />}
          />
          <MetricCard
            label="Trades"
            value={metrics.today.trades.toString()}
            subtitle={`${metrics.today.wins}W / ${metrics.today.losses}L`}
            icon={<BarChart2 size={18} />}
          />
          <MetricCard
            label="Win Rate"
            value={formatPercent(metrics.today.winRate)}
            icon={<Target size={18} />}
          />
          <MetricCard
            label="Drawdown"
            value={formatPercent(metrics.today.drawdown)}
            icon={<TrendingDown size={18} />}
          />
        </div>
      </div>

      {/* Account Metrics */}
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Account</h2>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
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
            label="Floating P&L"
            value={formatCurrency(metrics.account.floatingPL)}
            valueClass={getPnlClass(metrics.account.floatingPL)}
            icon={<ArrowDownUp size={18} />}
          />
        </div>
      </div>

      {/* Equity Curve */}
      <EquityCurve data={mockEquityCurve} />

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent Activity (takes 2 cols) */}
        <div className="lg:col-span-2">
          <RecentActivity activities={mockActivities} />
        </div>

        {/* System Health + Risk */}
        <div className="space-y-4">
          <SystemHealth items={mockSystemHealth} />
          <RiskStatusCard risk={mockRiskStatus} />
        </div>
      </div>

      {/* Overall Stats */}
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Overall</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard
            label="Total Trades"
            value={metrics.overall.totalTrades.toString()}
            icon={<Hash size={18} />}
          />
          <MetricCard
            label="Win Rate"
            value={formatPercent(metrics.overall.winRate)}
            icon={<Percent size={18} />}
          />
          <MetricCard
            label="Total P&L"
            value={formatCurrency(metrics.overall.totalPnl)}
            valueClass={getPnlClass(metrics.overall.totalPnl)}
            icon={<TrendingUp size={18} />}
          />
          <MetricCard
            label="Profit Factor"
            value={metrics.overall.profitFactor.toFixed(2)}
            icon={<Award size={18} />}
          />
        </div>
      </div>
    </div>
  );
}
