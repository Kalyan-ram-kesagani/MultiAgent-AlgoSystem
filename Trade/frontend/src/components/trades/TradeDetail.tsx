import type { Trade } from '@/types';
import { Badge } from '@/components/ui/Badge';
import { formatCurrency, formatPrice, formatDateTime, getPnlClass, formatPercent } from '@/utils/format';
import { X, Sparkles } from 'lucide-react';

interface TradeDetailProps {
  trade: Trade;
  onClose: () => void;
}

export function TradeDetail({ trade, onClose }: TradeDetailProps) {
  const rr =
    trade.stopLoss && trade.takeProfit && trade.entryPrice
      ? Math.abs(trade.takeProfit - trade.entryPrice) /
        Math.abs(trade.entryPrice - trade.stopLoss)
      : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md h-full bg-surface-raised border-l border-border overflow-y-auto animate-slide-in">
        {/* Header */}
        <div className="sticky top-0 bg-surface-raised z-10 flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <h2 className="text-base font-semibold text-text-primary">Trade #{trade.id.split('-')[1]}</h2>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={trade.result === 'WIN' ? 'success' : trade.result === 'LOSS' ? 'danger' : 'neutral'}>
                {trade.result ?? trade.status}
              </Badge>
              <span className="text-xs text-text-muted">{trade.status}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-surface-overlay text-text-muted transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Symbol & Direction */}
          <div className="flex items-center gap-3">
            <div className="px-3 py-1.5 rounded-lg bg-surface-overlay">
              <span className="text-sm font-bold text-text-primary">{trade.symbol}</span>
            </div>
            <Badge variant={trade.direction === 'BUY' ? 'success' : 'danger'}>
              {trade.direction}
            </Badge>
          </div>

          {/* Price Info */}
          <Section title="Prices">
            <Row label="Entry Price" value={formatPrice(trade.entryPrice)} />
            <Row label="Exit Price" value={formatPrice(trade.exitPrice)} />
            <Row label="Stop Loss" value={formatPrice(trade.stopLoss)} />
            <Row label="Take Profit" value={formatPrice(trade.takeProfit)} />
            <Row label="Lot Size" value={trade.volume.toFixed(2)} />
          </Section>

          {/* Time */}
          <Section title="Timing">
            <Row label="Entry Time" value={formatDateTime(trade.entryTime)} />
            <Row label="Exit Time" value={formatDateTime(trade.exitTime)} />
          </Section>

          {/* Result */}
          <Section title="Result">
            <Row
              label="P&L"
              value={trade.profitLoss !== null ? formatCurrency(trade.profitLoss) : '—'}
              valueClass={trade.profitLoss !== null ? getPnlClass(trade.profitLoss) : undefined}
            />
            <Row label="Commission" value={formatCurrency(trade.commission)} />
            <Row label="Swap" value={formatCurrency(trade.swap)} />
            {rr !== null && <Row label="R:R" value={`1:${rr.toFixed(1)}`} />}
          </Section>

          {/* Risk Management */}
          <Section title="Risk Management">
            <Row
              label="Initial Risk"
              value={
                trade.initialRiskPercent !== null
                  ? `${formatPercent(trade.initialRiskPercent)} ($${trade.initialRiskAmount?.toFixed(2)})`
                  : '—'
              }
            />
            <div className="flex items-center justify-between py-1.5">
              <span className="text-xs text-text-secondary">Risk-Free</span>
              <Badge
                variant={
                  trade.riskFreeStatus === 'YES'
                    ? 'success'
                    : trade.riskFreeStatus === 'NO'
                    ? 'danger'
                    : 'neutral'
                }
              >
                {trade.riskFreeStatus}
              </Badge>
            </div>
            {trade.breakEvenPrice && (
              <Row label="Break-Even Price" value={formatPrice(trade.breakEvenPrice)} />
            )}
            {trade.riskFreeActivatedTime && (
              <Row label="Risk-Free Activated" value={formatDateTime(trade.riskFreeActivatedTime)} />
            )}
          </Section>

          {/* Strategy */}
          <Section title="Strategy">
            <Row label="Strategy" value={trade.strategyName ?? '—'} />
          </Section>

          {/* AI Analysis Placeholder */}
          <div className="rounded-lg border border-border bg-surface-overlay px-4 py-6 text-center">
            <Sparkles size={20} className="mx-auto text-text-muted mb-2 opacity-40" />
            <p className="text-sm font-medium text-text-secondary">AI Analysis</p>
            <p className="text-xs text-text-muted mt-1">Coming soon</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-2">{title}</h3>
      <div className="space-y-0">{children}</div>
    </div>
  );
}

function Row({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border/50 last:border-0">
      <span className="text-xs text-text-secondary">{label}</span>
      <span className={`text-sm font-medium ${valueClass ?? 'text-text-primary'}`}>{value}</span>
    </div>
  );
}
