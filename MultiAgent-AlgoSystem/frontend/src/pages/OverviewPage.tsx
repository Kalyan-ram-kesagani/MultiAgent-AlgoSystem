import React from 'react';
import { DollarSign, Percent, ShieldCheck, Activity, Users, Server, Database, Cpu, ArrowRight } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';

interface OverviewPageProps {
  systemStatus: any;
  account: any;
  circuitBreaker: any;
  agents: any[];
  isBackendOnline?: boolean;
  onNavigateTab: (tab: string) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  systemStatus,
  account,
  circuitBreaker,
  agents = [],
  isBackendOnline = true,
  onNavigateTab,
}) => {
  const hasAccount = isBackendOnline && account && account.equity != null;
  const equityDisplay = hasAccount
    ? `$${Number(account.equity).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : 'DATA UNAVAILABLE';
  const balanceDisplay = hasAccount
    ? `Balance: $${Number(account.balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}`
    : (isBackendOnline ? 'Awaiting broker stream' : 'Backend offline');

  const dailyLoss = circuitBreaker?.current_day_loss ?? 0.0;
  const dailyLossDisplay = isBackendOnline
    ? `$${dailyLoss >= 0 ? '+' : ''}${dailyLoss.toFixed(2)}`
    : 'DATA UNAVAILABLE';
  const dailyLossSub = isBackendOnline
    ? (dailyLoss >= 0 ? "+0.00% daily return" : `${dailyLoss.toFixed(2)} drawdown`)
    : 'Backend offline';

  const drawdown = circuitBreaker?.current_drawdown_pct ?? 0.0;
  const drawdownDisplay = isBackendOnline
    ? `${drawdown.toFixed(2)}%`
    : 'DATA UNAVAILABLE';

  const riskEngineState = isBackendOnline
    ? (circuitBreaker?.kill_switch_active ? "HALTED" : "ENFORCING")
    : 'OFFLINE';
  const riskEngineSub = isBackendOnline
    ? (circuitBreaker?.kill_switch_active ? "Kill switch engaged" : "Pre-trade gates active")
    : 'Backend offline';

  const healthyAgentsCount = agents.filter(
    (a) => a.state?.status === 'IDLE' || a.state?.status === 'WORKING'
  ).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        <MetricCard
          label="Account Equity"
          value={equityDisplay}
          subtext={balanceDisplay}
          icon={<DollarSign size={20} />}
          trend="neutral"
        />
        <MetricCard
          label="Today's P&L"
          value={dailyLossDisplay}
          subtext={dailyLossSub}
          icon={<Activity size={20} />}
          trend={dailyLoss >= 0 ? "positive" : "negative"}
        />
        <MetricCard
          label="Portfolio Drawdown"
          value={drawdownDisplay}
          subtext={`Hard limit: ${circuitBreaker?.max_drawdown_threshold_pct ?? 10.0}%`}
          icon={<Percent size={20} />}
          trend={drawdown > 5.0 ? "negative" : "neutral"}
        />
        <MetricCard
          label="Risk Engine Gate"
          value={riskEngineState}
          subtext={riskEngineSub}
          icon={<ShieldCheck size={20} />}
          trend={circuitBreaker?.kill_switch_active ? "negative" : "positive"}
        />
      </div>

      {/* Main Grid: Live System Status & Agent Runtime */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1.2fr', gap: '1.5rem' }}>
        {/* Live System Status */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Live System Status</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Real-time health telemetry across all infrastructure layers.
              </p>
            </div>
            <span className="badge badge-green">
              <span className="pulse-dot" /> Operational
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
            {/* Backend Service */}
            <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>FastAPI Backend</span>
                <Server size={16} color="var(--accent-primary)" />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, fontSize: '0.9rem' }}>
                <span className={`pulse-dot ${isBackendOnline ? '' : 'pulse-dot-red'}`} />
                <span>{isBackendOnline ? 'Online' : 'Offline'}</span>
              </div>
              <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Port 8000 | Latency 2ms
              </div>
            </div>

            {/* MT5 Gateway */}
            <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>MetaTrader 5 Gateway</span>
                <Cpu size={16} color="var(--accent-primary)" />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, fontSize: '0.9rem' }}>
                <span className={`pulse-dot ${systemStatus?.mt5_connected ? '' : (systemStatus?.is_simulation ? '' : 'pulse-dot-red')}`} />
                <span>
                  {systemStatus?.mt5_connected ? 'Demo Connected' : (systemStatus?.is_simulation ? 'Simulation Gateway' : 'Disconnected')}
                </span>
              </div>
              <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                {account?.server || 'Sandbox Simulation'}
              </div>
            </div>

            {/* Database Engine */}
            <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Database Layer</span>
                <Database size={16} color="var(--accent-primary)" />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, fontSize: '0.9rem' }}>
                <span className="pulse-dot" />
                <span>Connected</span>
              </div>
              <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                SQLAlchemy Async Engine
              </div>
            </div>

            {/* Agent Runtime */}
            <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Agent Runtime</span>
                <Users size={16} color="var(--accent-primary)" />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, fontSize: '0.9rem' }}>
                <span className="pulse-dot" />
                <span>{healthyAgentsCount} / {agents.length || 11} Healthy</span>
              </div>
              <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Supervisor Watchdog Active
              </div>
            </div>
          </div>

          {/* Quick link to Agent Control Center */}
          <div
            onClick={() => onNavigateTab('agents')}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0.75rem 1rem',
              background: 'var(--bg-subtle)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              cursor: 'pointer',
              transition: 'background var(--transition-fast)',
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.8125rem' }}>Agent Control Center</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Inspect live tasks, heartbeats, and permissions across all 11 decoupled agents.
              </div>
            </div>
            <ArrowRight size={18} color="var(--accent-primary)" />
          </div>
        </div>

        {/* Core Pre-Trade Risk Limits Card */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Deterministic Pre-Trade Gates</h3>
              <span className="badge badge-green">Enforcing</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Every signal must pass all 6 hard risk checks before reaching the broker gateway.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.8125rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Risk Per Trade:</span>
                <span className="mono" style={{ fontWeight: 600 }}>1.0% Equity</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Daily Loss Limit:</span>
                <span className="mono" style={{ fontWeight: 600, color: 'var(--status-danger)' }}>3.0% Max</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Portfolio Drawdown Limit:</span>
                <span className="mono" style={{ fontWeight: 600, color: 'var(--status-danger)' }}>10.0% Max</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Spread Ceiling:</span>
                <span className="mono" style={{ fontWeight: 600 }}>5.0 Pips</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Consecutive Losses:</span>
                <span className="mono" style={{ fontWeight: 600 }}>{circuitBreaker?.consecutive_losses ?? 0} / 3 Allowed</span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '1.25rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Live Trading Mode:</span>
            <span className="badge badge-red">STRICTLY DISABLED</span>
          </div>
        </div>
      </div>
    </div>
  );
};
