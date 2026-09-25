import { MetricCard } from '@/components/ui/MetricCard';
import { Badge } from '@/components/ui/Badge';
import { mockAnalytics } from '@/services/mockData';
import { useAccount } from '@/hooks/useAccount';
import { formatCurrency, formatPercent, getPnlClass, cn } from '@/utils/format';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Target,
  Award,
  Clock,
  Sparkles,
  BarChart3,
  Percent,
  Zap,
} from 'lucide-react';

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.[0]) return null;
  return (
    <div className="bg-surface-overlay border border-border rounded-lg px-3 py-2 shadow-lg">
      <p className="text-xs text-text-muted mb-0.5">{label}</p>
      <p className={cn('text-sm font-semibold', getPnlClass(payload[0].value))}>
        {formatCurrency(payload[0].value)}
      </p>
    </div>
  );
}

export default function Analysis() {
  const { isAllAccounts, selectedAccount } = useAccount();
  const analytics = mockAnalytics;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">Analysis</h1>
        <p className="text-sm text-text-secondary mt-0.5">
          {isAllAccounts ? 'All Accounts' : selectedAccount?.accountName} · Trading performance overview
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          label="Win Rate"
          value={formatPercent(analytics.winRate)}
          icon={<Target size={18} />}
        />
        <MetricCard
          label="Profit Factor"
          value={analytics.profitFactor.toFixed(2)}
          icon={<Award size={18} />}
        />
        <MetricCard
          label="Avg Win"
          value={formatCurrency(analytics.avgWin)}
          valueClass="text-profit"
          icon={<TrendingUp size={18} />}
        />
        <MetricCard
          label="Avg Loss"
          value={formatCurrency(analytics.avgLoss)}
          valueClass="text-loss"
          icon={<TrendingDown size={18} />}
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          label="Total Trades"
          value={analytics.totalTrades.toString()}
          icon={<BarChart3 size={18} />}
        />
        <MetricCard
          label="Best Trade"
          value={formatCurrency(analytics.bestTrade)}
          valueClass="text-profit"
          icon={<Zap size={18} />}
        />
        <MetricCard
          label="Worst Trade"
          value={formatCurrency(analytics.worstTrade)}
          valueClass="text-loss"
          icon={<TrendingDown size={18} />}
        />
        <MetricCard
          label="Avg Hold Time"
          value={analytics.avgHoldTime}
          icon={<Clock size={18} />}
        />
      </div>

      {/* Monthly P&L Chart */}
      <div className="card">
        <h3 className="text-sm font-medium text-text-primary mb-4">Monthly P&L</h3>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={analytics.monthlyPnl} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
              <XAxis
                dataKey="month"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                tickFormatter={(val) => `$${val}`}
                width={50}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="pnl" radius={[4, 4, 0, 0]} animationDuration={600}>
                {analytics.monthlyPnl.map((entry, index) => (
                  <Cell key={index} fill={entry.pnl >= 0 ? 'var(--profit)' : 'var(--loss)'} opacity={0.8} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Symbol Breakdown */}
      <div className="card">
        <h3 className="text-sm font-medium text-text-primary mb-4">Symbol Performance</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                {['Symbol', 'Trades', 'Win Rate', 'P&L'].map((h) => (
                  <th key={h} className="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {analytics.symbolBreakdown.map((item) => (
                <tr key={item.symbol} className="border-b border-border/50 last:border-0 hover:bg-surface-overlay transition-colors">
                  <td className="px-4 py-2.5 font-medium text-text-primary">{item.symbol}</td>
                  <td className="px-4 py-2.5 text-text-secondary">{item.trades}</td>
                  <td className="px-4 py-2.5 text-text-secondary">{formatPercent(item.winRate)}</td>
                  <td className={cn('px-4 py-2.5 font-semibold', getPnlClass(item.pnl))}>
                    {formatCurrency(item.pnl)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Strategy Breakdown */}
      <div className="card">
        <h3 className="text-sm font-medium text-text-primary mb-4">Strategy Performance</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                {['Strategy', 'Trades', 'Win Rate', 'P&L'].map((h) => (
                  <th key={h} className="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {analytics.strategyBreakdown.map((item) => (
                <tr key={item.strategy} className="border-b border-border/50 last:border-0 hover:bg-surface-overlay transition-colors">
                  <td className="px-4 py-2.5 font-medium text-text-primary">{item.strategy}</td>
                  <td className="px-4 py-2.5 text-text-secondary">{item.trades}</td>
                  <td className="px-4 py-2.5 text-text-secondary">{formatPercent(item.winRate)}</td>
                  <td className={cn('px-4 py-2.5 font-semibold', getPnlClass(item.pnl))}>
                    {formatCurrency(item.pnl)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {['Winning Trade Analysis', 'Losing Trade Analysis', 'Pattern Detection', 'Market Regime Analysis'].map((title) => (
          <div key={title} className="card flex flex-col items-center justify-center py-8 text-center">
            <Sparkles size={20} className="text-text-muted mb-2 opacity-40" />
            <p className="text-sm font-medium text-text-secondary">{title}</p>
            <p className="text-xs text-text-muted mt-1">AI Analysis — Coming Soon</p>
          </div>
        ))}
      </div>
    </div>
  );
}
