import { useState } from 'react';
import { mockStrategies } from '@/services/mockData';
import { useAccount } from '@/hooks/useAccount';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { formatCurrency, formatPercent, getPnlClass, cn, formatDate } from '@/utils/format';
import { Layers, ArrowLeft, Sparkles, TrendingUp, TrendingDown, Target, BarChart2, Clock, Shield } from 'lucide-react';
import type { Strategy } from '@/types';

export default function Strategies() {
  const { isAllAccounts, selectedAccount } = useAccount();
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);

  if (selectedStrategy) {
    return <StrategyDetail strategy={selectedStrategy} onBack={() => setSelectedStrategy(null)} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">Strategies</h1>
        <p className="text-sm text-text-secondary mt-0.5">
          {mockStrategies.length} strategies · {isAllAccounts ? 'All Accounts' : selectedAccount?.accountName}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockStrategies.map((strategy) => (
          <div
            key={strategy.id}
            onClick={() => setSelectedStrategy(strategy)}
            className="card cursor-pointer hover:border-accent/30 transition-all duration-200 group"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold text-text-primary group-hover:text-accent transition-colors">
                  {strategy.name}
                </h3>
                <p className="text-xs text-text-muted mt-0.5">{strategy.version}</p>
              </div>
              <Badge
                variant={
                  strategy.status === 'active'
                    ? 'success'
                    : strategy.status === 'testing'
                    ? 'warning'
                    : 'neutral'
                }
              >
                {strategy.status.charAt(0).toUpperCase() + strategy.status.slice(1)}
              </Badge>
            </div>

            <p className="text-xs text-text-secondary line-clamp-2 mb-4">{strategy.description}</p>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-[10px] text-text-muted uppercase tracking-wider">Trades</p>
                <p className="text-sm font-semibold text-text-primary">{strategy.totalTrades}</p>
              </div>
              <div>
                <p className="text-[10px] text-text-muted uppercase tracking-wider">Win Rate</p>
                <p className="text-sm font-semibold text-text-primary">{formatPercent(strategy.winRate)}</p>
              </div>
              <div>
                <p className="text-[10px] text-text-muted uppercase tracking-wider">P&L</p>
                <p className={cn('text-sm font-semibold', getPnlClass(strategy.profitLoss))}>
                  {formatCurrency(strategy.profitLoss)}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-text-muted uppercase tracking-wider">Max DD</p>
                <p className="text-sm font-semibold text-text-primary">{formatPercent(strategy.maxDrawdown)}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StrategyDetail({ strategy, onBack }: { strategy: Strategy; onBack: () => void }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-1.5 rounded-lg hover:bg-surface-overlay text-text-muted transition-colors"
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-xl font-semibold text-text-primary">{strategy.name}</h1>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-sm text-text-secondary">{strategy.version}</span>
            <Badge
              variant={
                strategy.status === 'active' ? 'success' : strategy.status === 'testing' ? 'warning' : 'neutral'
              }
            >
              {strategy.status.charAt(0).toUpperCase() + strategy.status.slice(1)}
            </Badge>
          </div>
        </div>
      </div>

      {/* Overview */}
      <div className="card">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Overview</h3>
        <p className="text-sm text-text-secondary leading-relaxed">{strategy.description}</p>
        <div className="mt-3 flex items-center gap-4 text-xs text-text-muted">
          <span className="flex items-center gap-1"><Clock size={12} /> Created {formatDate(strategy.createdAt)}</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="card">
          <p className="text-[10px] text-text-muted uppercase tracking-wider">Total Trades</p>
          <p className="text-xl font-semibold text-text-primary mt-1">{strategy.totalTrades}</p>
        </div>
        <div className="card">
          <p className="text-[10px] text-text-muted uppercase tracking-wider">Win Rate</p>
          <p className="text-xl font-semibold text-text-primary mt-1">{formatPercent(strategy.winRate)}</p>
        </div>
        <div className="card">
          <p className="text-[10px] text-text-muted uppercase tracking-wider">Total P&L</p>
          <p className={cn('text-xl font-semibold mt-1', getPnlClass(strategy.profitLoss))}>
            {formatCurrency(strategy.profitLoss)}
          </p>
        </div>
        <div className="card">
          <p className="text-[10px] text-text-muted uppercase tracking-wider">Max Drawdown</p>
          <p className="text-xl font-semibold text-text-primary mt-1">{formatPercent(strategy.maxDrawdown)}</p>
        </div>
      </div>

      {/* Rules */}
      <div className="card">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Trading Rules</h3>
        <ul className="space-y-2">
          {strategy.rules.map((rule, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
              <span className="text-text-muted mt-0.5 text-xs">{i + 1}.</span>
              {rule}
            </li>
          ))}
        </ul>
      </div>

      {/* Risk Parameters */}
      <div className="card">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Risk Parameters</h3>
        <div className="space-y-2">
          {Object.entries(strategy.riskParameters).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between py-1.5 border-b border-border/50 last:border-0">
              <span className="text-xs text-text-secondary capitalize">
                {key.replace(/([A-Z])/g, ' $1').trim()}
              </span>
              <span className="text-sm font-medium text-text-primary">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* AI Strategy Suggestions */}
      <div className="card flex flex-col items-center justify-center py-8 text-center">
        <Sparkles size={24} className="text-text-muted mb-3 opacity-40" />
        <p className="text-sm font-medium text-text-secondary">AI Strategy Analysis</p>
        <p className="text-xs text-text-muted mt-1 max-w-sm">
          AI-powered strategy improvement suggestions and version generation will be available in a future update.
        </p>
      </div>
    </div>
  );
}
