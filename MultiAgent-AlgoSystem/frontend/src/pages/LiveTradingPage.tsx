import React, { useState } from 'react';
import { Play, ArrowUpRight, ArrowDownRight, RefreshCw, CheckCircle2, XCircle } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';

interface LiveTradingPageProps {
  onProcessSignal: (signal: any) => Promise<any>;
  isBackendOnline?: boolean;
}

export const LiveTradingPage: React.FC<LiveTradingPageProps> = ({ onProcessSignal, isBackendOnline = true }) => {
  const [symbol, setSymbol] = useState('EURUSD');
  const [direction, setDirection] = useState('BUY');
  const [entryPrice, setEntryPrice] = useState(1.0850);
  const [stopLoss, setStopLoss] = useState(1.0820);
  const [takeProfit, setTakeProfit] = useState(1.0910);
  const [loading, setLoading] = useState(false);
  const [lastExecution, setLastExecution] = useState<any>(null);

  // Real-time signals stream: records live session executions only (no mock orders)
  const [signalsHistory, setSignalsHistory] = useState<any[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        strategy_id: 'strategy_v1',
        strategy_version: '1.0.0',
        symbol,
        direction,
        timeframe: 'H1',
        timestamp: new Date().toISOString(),
        suggested_entry: Number(entryPrice),
        suggested_sl: Number(stopLoss),
        suggested_tp: Number(takeProfit),
        risk_points: Math.abs(Number(entryPrice) - Number(stopLoss)),
      };
      const res = await onProcessSignal(payload);
      setLastExecution(res);
      if (res?.client_order_id) {
        setSignalsHistory([
          {
            id: res.client_order_id,
            strategy_id: 'strategy_v1',
            symbol,
            direction,
            time: 'Just now',
            entry: res.price,
            sl: Number(stopLoss),
            tp: Number(takeProfit),
            status: res.status,
            lots: res.quantity || 0.0,
          },
          ...signalsHistory,
        ]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }}>
        {/* Signal Dispatch Form (Routes to Risk Engine) */}
        <div className="glass-panel">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Interactive Signal Gateway
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
            Simulate a strategy signal. Every signal must pass pre-trade risk validation and sizing.
          </p>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Symbol</label>
                <select
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: 'rgba(0, 0, 0, 0.4)',
                    color: '#fff',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  <option value="EURUSD">EURUSD</option>
                  <option value="XAUUSD">XAUUSD</option>
                  <option value="GBPUSD">GBPUSD</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Direction</label>
                <select
                  value={direction}
                  onChange={(e) => setDirection(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: 'rgba(0, 0, 0, 0.4)',
                    color: '#fff',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  <option value="BUY">BUY (Long)</option>
                  <option value="SELL">SELL (Short)</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Entry</label>
                <input
                  type="number"
                  step="0.0001"
                  value={entryPrice}
                  onChange={(e) => setEntryPrice(parseFloat(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Stop Loss</label>
                <input
                  type="number"
                  step="0.0001"
                  value={stopLoss}
                  onChange={(e) => setStopLoss(parseFloat(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>Take Profit</label>
                <input
                  type="number"
                  step="0.0001"
                  value={takeProfit}
                  onChange={(e) => setTakeProfit(parseFloat(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', background: 'rgba(0, 0, 0, 0.4)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '0.5rem' }}
            >
              {loading ? <RefreshCw className="animate-spin" size={16} /> : <Play size={16} />}
              <span>Dispatch Signal via Risk Gate</span>
            </button>
          </form>

          {lastExecution && (
            <div style={{ marginTop: '1.25rem', padding: '0.75rem', background: 'rgba(0,0,0,0.3)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem' }}>
                {lastExecution.status === 'FILLED' ? (
                  <CheckCircle2 color="var(--accent-green)" size={16} />
                ) : (
                  <XCircle color="var(--accent-red)" size={16} />
                )}
                <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                  Order Status: {lastExecution.status}
                </span>
              </div>
              {lastExecution.quantity > 0 && (
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Sized: <span className="mono">{lastExecution.quantity} Lots</span> | Latency: <span className="mono">{lastExecution.latency_ms}ms</span>
                </div>
              )}
              {lastExecution.rejection_reasons && (
                <div style={{ fontSize: '0.75rem', color: 'var(--accent-red)' }}>
                  Rejection: {lastExecution.rejection_reasons.join(', ')}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Live Signals & Execution Audit Feed */}
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Signal & Order Audit Stream</h3>
            <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Real-time Gateway Feed</span>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Entry</th>
                <th>Stop / Target</th>
                <th>Lots</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {signalsHistory.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No orders submitted in this session. Dispatch a signal above to evaluate against the Risk Engine and MT5 Gateway.
                  </td>
                </tr>
              ) : (
                signalsHistory.map((s) => (
                  <tr key={s.id}>
                    <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>{s.id.slice(0, 10)}</td>
                    <td style={{ fontWeight: 600 }}>{s.symbol}</td>
                    <td>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.2rem',
                        color: s.direction === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)',
                        fontWeight: 700,
                      }}>
                        {s.direction === 'BUY' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                        {s.direction}
                      </span>
                    </td>
                    <td className="mono">{s.entry}</td>
                    <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      SL: {s.sl} | TP: {s.tp}
                    </td>
                    <td className="mono">{s.lots}</td>
                    <td>
                      <StatusBadge status={s.status} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
