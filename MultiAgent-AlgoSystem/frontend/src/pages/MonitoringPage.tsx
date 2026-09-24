import React, { useState } from 'react';
import { Server, Cpu, Database, ShieldAlert, Activity, RefreshCw } from 'lucide-react';
import { EventTimeline } from '../components/EventTimeline';
import { StatusBadge } from '../components/StatusBadge';

interface MonitoringPageProps {
  systemStatus: any;
  events: any[];
  isBackendOnline?: boolean;
  onRefreshEvents?: () => void;
}

export const MonitoringPage: React.FC<MonitoringPageProps> = ({
  systemStatus,
  events = [],
  isBackendOnline = true,
  onRefreshEvents,
}) => {
  const [filterLevel, setFilterLevel] = useState<string>('ALL');

  const filteredEvents = events.filter((e) => {
    if (filterLevel === 'ALL') return true;
    return e.level === filterLevel;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Infrastructure Telemetry Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        {/* Backend Node */}
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              FASTAPI BACKEND
            </span>
            <Server size={18} color="var(--accent-primary)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className={`pulse-dot ${isBackendOnline ? '' : 'pulse-dot-red'}`} />
            <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>
              {isBackendOnline ? 'Online & Healthy' : 'Offline'}
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
            Port 8000 | Latency 2ms | Pydantic v2
          </div>
        </div>

        {/* MT5 Gateway */}
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              METATRADER 5 LINK
            </span>
            <Cpu size={18} color="var(--accent-primary)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              className={`pulse-dot ${systemStatus?.mt5_connected ? '' : (systemStatus?.is_simulation ? '' : 'pulse-dot-red')}`}
            />
            <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>
              {systemStatus?.mt5_connected ? 'Native MT5 Active' : (systemStatus?.is_simulation ? 'Simulation Gateway' : 'Disconnected')}
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
            {systemStatus?.mt5_connected ? 'Demo Account Connected' : 'Auto-kill switch on disconnect'}
          </div>
        </div>

        {/* Database */}
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              DATABASE ENGINE
            </span>
            <Database size={18} color="var(--accent-primary)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="pulse-dot" />
            <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>SQLAlchemy Connected</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
            SQLite/PostgreSQL Dual Engine | Async
          </div>
        </div>

        {/* Risk Engine */}
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              DETERMINISTIC RISK GATE
            </span>
            <ShieldAlert size={18} color="var(--status-success)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="pulse-dot" />
            <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>Pre-Trade Sizing Enforcing</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
            Max DD: 10% | Daily: 3% | Max Spread: 5.0 pips
          </div>
        </div>
      </div>

      {/* Structured Observability Event Log */}
      <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>System Observability & Event Stream</h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Real-time audit trail of all signals, risk evaluations, order submissions, and agent state transitions.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <button
              onClick={() => setFilterLevel('ALL')}
              className={`btn btn-sm ${filterLevel === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
            >
              All Events
            </button>
            <button
              onClick={() => setFilterLevel('INFO')}
              className={`btn btn-sm ${filterLevel === 'INFO' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Info
            </button>
            <button
              onClick={() => setFilterLevel('WARNING')}
              className={`btn btn-sm ${filterLevel === 'WARNING' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Warnings
            </button>
            <button
              onClick={() => setFilterLevel('CRITICAL')}
              className={`btn btn-sm ${filterLevel === 'CRITICAL' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Critical
            </button>
            {onRefreshEvents && (
              <button onClick={onRefreshEvents} className="btn btn-secondary btn-sm" title="Refresh events">
                <RefreshCw size={13} />
              </button>
            )}
          </div>
        </div>

        {isBackendOnline ? (
          <EventTimeline events={filteredEvents} />
        ) : (
          <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--status-danger)' }}>
            DATA UNAVAILABLE (Backend Offline)
          </div>
        )}
      </div>
    </div>
  );
};
