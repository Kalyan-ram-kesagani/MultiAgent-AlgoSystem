import React, { useState, useEffect } from 'react';
import { Layers, CheckCircle, GitBranch, Shield, Sliders, History, Lock, FileText } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';

interface StrategiesPageProps {
  strategies: any[];
}

export const StrategiesPage: React.FC<StrategiesPageProps> = ({ strategies }) => {
  const [versions, setVersions] = useState<any[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);

  const fetchVersions = async () => {
    setLoadingVersions(true);
    try {
      const res = await fetch('/api/strategies/versions').catch(() => fetch('/api/v1/strategies/versions'));
      if (res && res.ok) {
        const data = await res.json();
        setVersions(Array.isArray(data) ? data : []);
      }
    } catch (e) {
      console.error('Failed to fetch strategy versions:', e);
    } finally {
      setLoadingVersions(false);
    }
  };

  useEffect(() => {
    fetchVersions();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div className="glass-panel" style={{ borderLeft: '4px solid var(--accent-cyan)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>Strategy Catalog & Immutable Version Registry</h2>
              <span className="badge badge-cyan">{strategies.length} Active Baseline</span>
              <span className="badge badge-neutral">{versions.length} Version Trackers</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem', marginBottom: 0 }}>
              Deterministic trading rule implementations. Every version is strictly immutable once validated.
              Baseline <code style={{ color: 'var(--accent-cyan)' }}>strategy_v1</code> is preserved and never overwritten.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#10b981', fontSize: '0.75rem', fontWeight: 600 }}>
            <Lock size={14} />
            <span>IMMUTABILITY ENFORCED</span>
          </div>
        </div>
      </div>

      {/* Baseline Strategies Cards */}
      <div>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          ACTIVE PRODUCTION BASELINE (READ-ONLY)
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
          {strategies.map((strat) => (
            <div key={strat.strategy_id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', border: '1px solid var(--accent-primary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>{strat.name}</h3>
                    <span className="mono badge badge-cyan">{strat.version}</span>
                  </div>
                  <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    ID: {strat.strategy_id} | Timeframe: {strat.timeframe}
                  </span>
                </div>
                <StatusBadge status="VALIDATED" />
              </div>

              <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', margin: 0 }}>
                {strat.description}
              </p>

              <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                  <Sliders size={14} />
                  <span>BASELINE DETERMINISTIC PARAMETERS</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', fontSize: '0.75rem' }}>
                  {strat.default_parameters && Object.entries(strat.default_parameters).map(([key, val]) => (
                    <div key={key} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.03)', paddingBottom: '2px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>{key}:</span>
                      <span className="mono" style={{ color: 'var(--accent-cyan)' }}>{String(val)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.5rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Supported Symbols:</span>
                <div style={{ display: 'flex', gap: '0.3rem' }}>
                  {strat.supported_symbols?.map((sym: string) => (
                    <span key={sym} className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>{sym}</span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Immutable Candidate Versions Lineage */}
      <div className="glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <History size={18} color="var(--accent-primary)" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>
              Immutable Strategy Version Lineage (strategy_versions Table)
            </h3>
          </div>
          <span className="mono badge badge-neutral" style={{ fontSize: '0.6875rem' }}>
            {versions.length} Candidate Iterations
          </span>
        </div>

        {versions.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {versions.map((ver) => (
              <div
                key={ver.id}
                style={{
                  background: 'rgba(0, 0, 0, 0.25)',
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.4rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span className="mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      {ver.strategy_id} &rarr; {ver.version}
                    </span>
                    <span className="badge badge-neutral" style={{ fontSize: '0.68rem' }}>
                      Author: {ver.author}
                    </span>
                  </div>
                  <span
                    className="badge"
                    style={{
                      background:
                        ver.status === 'APPROVED_FOR_DEMO'
                          ? 'rgba(16, 185, 129, 0.15)'
                          : 'rgba(245, 158, 11, 0.15)',
                      color:
                        ver.status === 'APPROVED_FOR_DEMO'
                          ? '#10b981'
                          : '#f59e0b',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                    }}
                  >
                    {ver.status}
                  </span>
                </div>

                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  <strong>Changelog:</strong> {ver.changelog}
                </div>

                {ver.parameters && (
                  <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: '0.5rem', borderRadius: '4px', fontSize: '0.72rem' }}>
                    <div style={{ color: 'var(--text-muted)', marginBottom: '0.25rem', fontWeight: 600 }}>Bounded Parameters:</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                      {Object.entries(ver.parameters).map(([k, v]) => (
                        <div key={k}>
                          <span style={{ color: 'var(--text-muted)' }}>{k}: </span>
                          <span className="mono" style={{ color: '#fff' }}>{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: 'var(--text-muted)', paddingTop: '0.3rem', borderTop: '1px solid rgba(255,255,255,0.03)' }}>
                  <span>Created: {new Date(ver.created_at).toLocaleString()}</span>
                  <span>Safety Status: Immutable candidate. Live trading locked.</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            No candidate versions recorded yet. As Orchestrator coordinates research tasks, candidate versions will be archived here immutably.
          </div>
        )}
      </div>
    </div>
  );
};
