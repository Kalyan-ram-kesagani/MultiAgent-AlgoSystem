import React, { useState } from 'react';
import { FileText, ArrowUpRight, ArrowDownRight, Filter, PieChart } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';

interface JournalPageProps {
  trades: any[];
  performance: any;
  isBackendOnline?: boolean;
}

export const JournalPage: React.FC<JournalPageProps> = ({ trades = [], performance, isBackendOnline = true }) => {
  const [selectedFilter, setSelectedFilter] = useState('ALL');

  const displayTrades = Array.isArray(trades) ? trades : [];
  const hasTrades = displayTrades.length > 0;
  const hasPerf = performance && typeof performance === 'object' && performance.total_trades !== undefined;

  // Derive metrics strictly from backend performance or indicate unavailable/zero
  let winRateVal = 'DATA UNAVAILABLE';
  let winRateSub = 'Backend offline';
  let profitFactorVal = 'DATA UNAVAILABLE';
  let profitFactorSub = 'Backend offline';
  let expectancyVal = 'DATA UNAVAILABLE';
  let expectancySub = 'Backend offline';
  let netPnlVal = 'DATA UNAVAILABLE';
  let netPnlSub = 'Backend offline';
  let trend: 'positive' | 'negative' | 'neutral' = 'neutral';

  if (isBackendOnline) {
    if (hasPerf && performance.total_trades > 0) {
      const rawWr = performance.win_rate ?? 0;
      const wr = rawWr > 1 ? rawWr : rawWr * 100;
      winRateVal = `${wr.toFixed(1)}%`;
      const winsCount = performance.winning_trades ?? Math.round((wr / 100) * performance.total_trades);
      const lossesCount = performance.losing_trades ?? (performance.total_trades - winsCount);
      winRateSub = `${winsCount} Wins / ${lossesCount} Losses`;

      profitFactorVal = performance.profit_factor != null ? Number(performance.profit_factor).toFixed(2) : 'N/A';
      profitFactorSub = performance.gross_profit != null
        ? `Gross Win $${Number(performance.gross_profit).toFixed(2)} / Loss $${Number(performance.gross_loss ?? 0).toFixed(2)}`
        : `Profit Factor: ${profitFactorVal}`;

      expectancyVal = `$${Number(performance.expectancy ?? 0).toFixed(2)}`;
      const avgR = performance.average_r ?? performance.avg_r_multiple ?? 0;
      expectancySub = `Avg R: ${Number(avgR).toFixed(2)}R`;

      const pnl = performance.total_net_pnl ?? performance.net_pnl ?? 0;
      netPnlVal = `${pnl >= 0 ? '+' : ''}$${Number(pnl).toFixed(2)}`;
      netPnlSub = `${performance.total_trades} closed trades in Supabase DB`;
      trend = pnl >= 0 ? 'positive' : 'negative';
    } else {
      winRateVal = '0.0%';
      winRateSub = '0 Wins / 0 Losses';
      profitFactorVal = '0.00';
      profitFactorSub = 'No closed trades';
      expectancyVal = '$0.00';
      expectancySub = 'Avg R: 0.00R';
      netPnlVal = '$0.00';
      netPnlSub = 'Awaiting closed positions in DB';
      trend = 'neutral';
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Performance Attribution Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <MetricCard
          label="Win Rate"
          value={winRateVal}
          subtext={winRateSub}
          trend={trend}
        />
        <MetricCard
          label="Profit Factor"
          value={profitFactorVal}
          subtext={profitFactorSub}
          trend={trend}
        />
        <MetricCard
          label="Expectancy"
          value={expectancyVal}
          subtext={expectancySub}
          trend={trend}
        />
        <MetricCard
          label="Total Net PnL"
          value={netPnlVal}
          subtext={netPnlSub}
          trend={trend}
        />
      </div>

      {/* Trade Log Table */}
      <div className="glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Automated Trade Journal Audit</h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Complete audit trail capturing prices, quantities, R-multiples, sessions, and market regimes from Supabase PostgreSQL database.
            </p>
          </div>
          <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-green)' }}>
            {displayTrades.length} Reconciled MT5 Trades
          </span>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Trade ID</th>
              <th>Strategy</th>
              <th>Symbol</th>
              <th>Side</th>
              <th>Entry / Exit Price</th>
              <th>Lots</th>
              <th>Net PnL</th>
              <th>R-Multiple</th>
              <th>Session</th>
              <th>Regime</th>
              <th>Exit</th>
            </tr>
          </thead>
          <tbody>
            {displayTrades.length === 0 ? (
              <tr>
                <td colSpan={11} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                  {isBackendOnline 
                    ? "No closed trade records found in database. Closed positions from MT5 / Simulation will automatically be logged here."
                    : "DATA UNAVAILABLE — Backend server is currently disconnected."}
                </td>
              </tr>
            ) : (
              displayTrades.map((t) => (
                <tr key={t.trade_id}>
                  <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>{t.trade_id}</td>
                  <td style={{ fontSize: '0.8rem' }}>{t.strategy_id}</td>
                  <td style={{ fontWeight: 600 }}>{t.symbol}</td>
                  <td>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.2rem',
                      color: t.direction === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)',
                      fontWeight: 700,
                    }}>
                      {t.direction === 'BUY' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                      {t.direction}
                    </span>
                  </td>
                  <td className="mono" style={{ fontSize: '0.75rem' }}>
                    {t.entry_price} → {t.exit_price}
                  </td>
                  <td className="mono">{t.quantity}</td>
                  <td className="mono" style={{ color: t.pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 700 }}>
                    ${t.pnl >= 0 ? '+' : ''}{Number(t.pnl).toFixed(2)}
                  </td>
                  <td className="mono" style={{ fontWeight: 600 }}>{t.r_multiple > 0 ? `+${t.r_multiple}R` : `${t.r_multiple}R`}</td>
                  <td><span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>{t.session}</span></td>
                  <td><span className="badge badge-amber" style={{ fontSize: '0.65rem' }}>{t.market_regime}</span></td>
                  <td><span className="badge badge-green" style={{ fontSize: '0.65rem' }}>{t.exit_reason}</span></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
