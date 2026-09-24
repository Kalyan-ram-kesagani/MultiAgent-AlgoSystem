import React, { useState } from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle, ShieldCheck, Sliders, RefreshCw } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';

interface RiskPageProps {
  circuitBreaker: any;
  onEmergencyClick: () => void;
  onEvaluateRisk: (req: any) => Promise<any>;
}

export const RiskPage: React.FC<RiskPageProps> = ({
  circuitBreaker,
  onEmergencyClick,
  onEvaluateRisk,
}) => {
  const [testEquity, setTestEquity] = useState(10000);
  const [symbol, setSymbol] = useState('EURUSD');
  const [side, setSide] = useState('BUY');
  const [entry, setEntry] = useState(1.0850);
  const [stop, setStop] = useState(1.0820);
  const [spread, setSpread] = useState(1.2);
  const [openPositions, setOpenPositions] = useState(1);
  const [evalResult, setEvalResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleTestEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await onEvaluateRisk({
        strategy_id: 'strategy_v1',
        symbol,
        side,
        entry_price: Number(entry),
        stop_loss: Number(stop),
        take_profit: Number(entry) + Math.abs(Number(entry) - Number(stop)) * 2,
        account_equity: Number(testEquity),
        account_balance: Number(testEquity),
        current_spread_pips: Number(spread),
        open_positions_count: Number(openPositions),
        symbol_positions_count: 0,
      });
      setEvalResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Circuit Breakers & Emergency Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        <MetricCard
          label="Kill Switch"
          value={circuitBreaker?.kill_switch_active ? "ENGAGED" : "ARMED"}
          subtext={circuitBreaker?.kill_switch_active ? "Trading strictly halted" : "Pre-trade gate enforcing"}
          trend={circuitBreaker?.kill_switch_active ? "negative" : "positive"}
          icon={<ShieldAlert size={20} />}
        />
        <MetricCard
          label="Max Daily Loss Limit"
          value={`${circuitBreaker?.max_daily_loss_threshold_pct ?? 3.0}%`}
          subtext="Circuit breaker threshold"
          trend="neutral"
        />
        <MetricCard
          label="Max Drawdown Limit"
          value={`${circuitBreaker?.max_drawdown_threshold_pct ?? 10.0}%`}
          subtext="Portfolio emergency stop"
          trend="neutral"
        />
        <MetricCard
          label="Consecutive Losses"
          value={`${circuitBreaker?.consecutive_losses ?? 0} / 3`}
          subtext="Auto-halt on 3 consecutive losses"
          trend={circuitBreaker?.consecutive_losses > 1 ? "negative" : "positive"}
        />
      </div>

      {/* Sizing & Pre-Trade Simulation Engine */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem' }}>
        <div className="glass-panel">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Pre-Trade Sizing & Rule Gate Simulator
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
            Simulate how the Risk Engine calculates exact lots from stop distance and enforces hard limits.
          </p>

          <form onSubmit={handleTestEvaluation} style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Account Equity ($)</label>
                <input
                  type="number"
                  value={testEquity}
                  onChange={(e) => setTestEquity(parseFloat(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Symbol</label>
                <select
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                >
                  <option value="EURUSD">EURUSD</option>
                  <option value="XAUUSD">XAUUSD</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Entry</label>
                <input
                  type="number"
                  step="0.0001"
                  value={entry}
                  onChange={(e) => setEntry(parseFloat(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Stop Loss</label>
                <input
                  type="number"
                  step="0.0001"
                  value={stop}
                  onChange={(e) => setStop(parseFloat(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Spread (Pips)</label>
                <input
                  type="number"
                  step="0.1"
                  value={spread}
                  onChange={(e) => setSpread(parseFloat(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-secondary"
              style={{ width: '100%', marginTop: '0.5rem' }}
            >
              {loading ? <RefreshCw className="animate-spin" size={16} /> : <Sliders size={16} />}
              <span>Test Pre-Trade Gate Validation</span>
            </button>
          </form>

          {evalResult && (
            <div style={{
              marginTop: '1.25rem',
              padding: '1rem',
              background: evalResult.is_approved ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
              border: `1px solid ${evalResult.is_approved ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              borderRadius: 'var(--radius-sm)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontWeight: 700, color: evalResult.is_approved ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                  GATE RESULT: {evalResult.is_approved ? 'APPROVED' : 'REJECTED'}
                </span>
                <span className="mono" style={{ fontSize: '0.85rem', fontWeight: 700 }}>
                  Calculated Lots: {evalResult.calculated_lots}
                </span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Risk Allocation: <span className="mono">${evalResult.risk_amount_dollars} ({evalResult.risk_percentage}%)</span> | Stop Distance: <span className="mono">{evalResult.stop_distance_points}</span>
              </div>
              {evalResult.rejection_reasons?.length > 0 && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--accent-red)' }}>
                  Violations: {evalResult.rejection_reasons.join('; ')}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Emergency Halt Console */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--accent-red)' }}>
              Master Emergency Kill Switch
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              The hard kill switch instantly disables all automated trading pipelines. No strategy or agent can bypass it.
            </p>
            <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.8rem' }}>
              <div style={{ color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Active Status:</div>
              <div style={{ fontWeight: 700, color: circuitBreaker?.kill_switch_active ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                {circuitBreaker?.kill_switch_active ? 'HALTED — ALL NEW TRADES BLOCKED' : 'ARMED & MONITORING SAFETY LIMITS'}
              </div>
              {circuitBreaker?.pause_reason && (
                <div style={{ marginTop: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                  Reason: {circuitBreaker.pause_reason}
                </div>
              )}
            </div>
          </div>

          <button
            onClick={onEmergencyClick}
            className={`btn ${circuitBreaker?.kill_switch_active ? 'btn-primary' : 'btn-danger'}`}
            style={{ width: '100%', padding: '0.75rem' }}
          >
            <ShieldAlert size={18} />
            <span>{circuitBreaker?.kill_switch_active ? 'Reset & Disengage Kill Switch' : '🛑 ENGAGE EMERGENCY STOP'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
