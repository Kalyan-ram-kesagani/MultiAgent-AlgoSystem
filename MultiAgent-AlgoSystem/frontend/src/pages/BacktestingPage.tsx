import React, { useState } from 'react';
import { Play, TrendingUp, BarChart2, ShieldAlert, CheckCircle, RefreshCw } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';

interface BacktestingPageProps {
  onRunBacktest: (req: any) => Promise<any>;
}

export const BacktestingPage: React.FC<BacktestingPageProps> = ({ onRunBacktest }) => {
  const [strategyId, setStrategyId] = useState('strategy_v1');
  const [symbol, setSymbol] = useState('EURUSD');
  const [timeframe, setTimeframe] = useState('H1');
  const [capital, setCapital] = useState(10000);
  const [spreadPips, setSpreadPips] = useState(1.5);
  const [slippagePoints, setSlippagePoints] = useState(5);
  const [runMonteCarlo, setRunMonteCarlo] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await onRunBacktest({
        strategy_id: strategyId,
        strategy_version: '1.0.0',
        symbol,
        timeframe,
        initial_capital: Number(capital),
        spread_pips: Number(spreadPips),
        slippage_points: Number(slippagePoints),
        run_monte_carlo: runMonteCarlo,
        monte_carlo_iterations: 150,
      });
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Helper to render SVG equity line
  const renderEquityChart = (equityCurve: any[]) => {
    if (!equityCurve || equityCurve.length < 2) return null;
    const values = equityCurve.map((pt) => pt.equity);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const range = maxVal - minVal || 1;
    const width = 600;
    const height = 140;

    const points = values
      .map((val, idx) => {
        const x = (idx / (values.length - 1)) * width;
        const y = height - ((val - minVal) / range) * (height - 20) - 10;
        return `${x},${y}`;
      })
      .join(' ');

    return (
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: '160px', overflow: 'visible' }}>
        <defs>
          <linearGradient id="eqGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
          </linearGradient>
        </defs>
        <polyline
          fill="none"
          stroke="var(--accent-cyan)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
      </svg>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2.5fr', gap: '1.5rem' }}>
        {/* Backtest Parameters Form */}
        <div className="glass-panel">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Backtest Simulation Engine
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
            Simulates realistic execution including spread, slippage, and broker commissions.
          </p>

          <form onSubmit={handleRun} style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Strategy</label>
              <select
                value={strategyId}
                onChange={(e) => setStrategyId(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
              >
                <option value="strategy_v1">strategy_v1 (Trend Pullback)</option>
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Symbol</label>
                <select
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                >
                  <option value="EURUSD">EURUSD</option>
                  <option value="XAUUSD">XAUUSD</option>
                  <option value="GBPUSD">GBPUSD</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Timeframe</label>
                <select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                >
                  <option value="H1">H1 (1 Hour)</option>
                  <option value="M15">M15 (15 Min)</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Capital ($)</label>
                <input
                  type="number"
                  value={capital}
                  onChange={(e) => setCapital(parseFloat(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Spread (Pips)</label>
                <input
                  type="number"
                  step="0.1"
                  value={spreadPips}
                  onChange={(e) => setSpreadPips(parseFloat(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
              <input
                type="checkbox"
                id="mcCheck"
                checked={runMonteCarlo}
                onChange={(e) => setRunMonteCarlo(e.target.checked)}
              />
              <label htmlFor="mcCheck" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Run Monte Carlo 95% Permutation Analysis
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '0.5rem' }}
            >
              {loading ? <RefreshCw className="animate-spin" size={16} /> : <Play size={16} />}
              <span>Execute Rigorous Backtest</span>
            </button>
          </form>
        </div>

        {/* Results & Equity Curve */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {result ? (
            <>
              {/* Performance Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
                <MetricCard
                  label="Net Profit"
                  value={`$${result.net_profit >= 0 ? '+' : ''}${result.net_profit.toFixed(2)}`}
                  trend={result.net_profit >= 0 ? 'positive' : 'negative'}
                />
                <MetricCard
                  label="Win Rate"
                  value={`${result.win_rate.toFixed(1)}%`}
                  subtext={`${result.winning_trades}W / ${result.losing_trades}L (${result.total_trades} total)`}
                  trend={result.win_rate >= 50 ? 'positive' : 'neutral'}
                />
                <MetricCard
                  label="Profit Factor"
                  value={result.profit_factor >= 999 ? '∞' : result.profit_factor.toFixed(2)}
                  subtext={`Expectancy: $${result.expectancy.toFixed(2)}`}
                  trend={result.profit_factor >= 1.5 ? 'positive' : 'neutral'}
                />
                <MetricCard
                  label="Max Drawdown"
                  value={`${result.max_drawdown_pct.toFixed(2)}%`}
                  subtext={result.monte_carlo_drawdown_95 ? `MC 95%: ${result.monte_carlo_drawdown_95.toFixed(1)}%` : `Sharpe: ${result.sharpe_ratio}`}
                  trend={result.max_drawdown_pct <= 5.0 ? 'positive' : 'negative'}
                />
              </div>

              {/* Equity Chart */}
              <div className="glass-panel">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>SIMULATED EQUITY TRAJECTORY</h4>
                  <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>
                    {result.backtest_id}
                  </span>
                </div>
                {renderEquityChart(result.equity_curve)}
              </div>

              {/* Trade Log */}
              <div className="glass-panel">
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>EXECUTED TRADES AUDIT</h4>
                <div style={{ maxHeight: '180px', overflowY: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Direction</th>
                        <th>Entry Price</th>
                        <th>Exit Price</th>
                        <th>Lots</th>
                        <th>PnL</th>
                        <th>R</th>
                        <th>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.trades?.slice(0, 10).map((t: any, idx: number) => (
                        <tr key={idx}>
                          <td style={{ color: t.direction === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 600 }}>
                            {t.direction}
                          </td>
                          <td className="mono">{t.entry_price}</td>
                          <td className="mono">{t.exit_price}</td>
                          <td className="mono">{t.quantity}</td>
                          <td className="mono" style={{ color: t.pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 600 }}>
                            ${t.pnl.toFixed(2)}
                          </td>
                          <td className="mono">{t.r_multiple}R</td>
                          <td>
                            <span className="badge badge-cyan">{t.exit_reason}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="glass-panel" style={{ textAlign: 'center', padding: '3.5rem 1rem', color: 'var(--text-muted)' }}>
              <TrendingUp size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>No Backtest Executed Yet</h3>
              <p style={{ fontSize: '0.8rem', maxWidth: '400px', margin: '0.5rem auto' }}>
                Configure parameters and click "Execute Rigorous Backtest" to evaluate performance under spread, slippage, and Monte Carlo permutations.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
