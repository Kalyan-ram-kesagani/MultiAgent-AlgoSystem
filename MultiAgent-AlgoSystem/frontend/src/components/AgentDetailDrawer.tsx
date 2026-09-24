import React from 'react';
import { X, ShieldCheck, Wrench, Layers, Check, Ban, Clock, Terminal, Cpu } from 'lucide-react';
import { StatusBadge } from './StatusBadge';

interface AgentDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  agent: {
    metadata: {
      agent_id: string;
      name: string;
      description: string;
      role: string;
      agent_type: string;
      version: string;
      capabilities: string[];
      permissions: string[];
      tools: string[];
      model?: string;
    };
    state: {
      agent_id: string;
      name: string;
      status: string;
      heartbeat_timestamp: string;
      current_task?: string;
      last_task?: string;
      last_result?: string;
      tasks_completed_today: number;
      error_message?: string;
    };
  } | null;
}

export const AgentDetailDrawer: React.FC<AgentDetailDrawerProps> = ({ isOpen, onClose, agent }) => {
  if (!isOpen || !agent) return null;

  const { metadata, state } = agent;
  const isAi = metadata.agent_type === 'AI_REASONING';

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.65)',
        backdropFilter: 'blur(4px)',
        zIndex: 50,
        display: 'flex',
        justifyContent: 'flex-end',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '520px',
          height: '100%',
          backgroundColor: 'var(--bg-surface-elevated)',
          borderLeft: '1px solid var(--border-medium)',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: 'var(--shadow-lg)',
          animation: 'slideInRight 0.2s ease-out',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{metadata.name}</h2>
              <StatusBadge status={state.status} />
            </div>
            <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              ID: {metadata.agent_id} | Version: {metadata.version}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '0.4rem',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Overview */}
          <div>
            <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
              Role & Responsibility
            </h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {metadata.description}
            </p>
          </div>

          {/* AI Model Spec (If AI Reasoning Agent) */}
          {isAi && (
            <div
              style={{
                background: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.85rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.3rem' }}>
                <Cpu size={16} color="#818cf8" />
                <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: '#a5b4fc' }}>AI Reasoning Architecture</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                <strong>Reasoning Engine:</strong> {metadata.model || 'Deterministic ML + Structured Reasoning Engine'}
              </div>
              <div style={{ fontSize: '0.71875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Bound by deterministic pre-trade gates. Cannot directly submit broker orders or alter safety limits.
              </div>
            </div>
          )}

          {/* Capabilities */}
          <div>
            <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              Operational Capabilities
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {metadata.capabilities?.map((cap) => (
                <span key={cap} className="badge badge-cyan" style={{ fontSize: '0.6875rem' }}>
                  {cap}
                </span>
              ))}
            </div>
          </div>

          {/* Tools */}
          <div>
            <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              Attached Tools
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {metadata.tools?.map((tool) => (
                <span key={tool} className="badge badge-neutral mono" style={{ fontSize: '0.6875rem' }}>
                  <Wrench size={12} style={{ marginRight: '0.25rem' }} />
                  {tool}
                </span>
              ))}
            </div>
          </div>

          {/* Permissions (CAN vs CANNOT) */}
          <div>
            <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              Security Permissions & Boundaries
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.78125rem' }}>
              {metadata.permissions?.map((perm) => (
                <div key={perm} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--status-success)' }}>
                  <Check size={14} />
                  <span className="mono" style={{ color: 'var(--text-primary)' }}>CAN: {perm}</span>
                </div>
              ))}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--status-danger)' }}>
                <Ban size={14} />
                <span className="mono" style={{ color: 'var(--text-muted)' }}>CANNOT: Bypass Risk Engine</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--status-danger)' }}>
                <Ban size={14} />
                <span className="mono" style={{ color: 'var(--text-muted)' }}>CANNOT: Activate Live Trading Mode</span>
              </div>
            </div>
          </div>

          {/* Task History / Diagnostic Telemetry */}
          <div>
            <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              Execution Telemetry
            </h4>
            <div
              style={{
                background: 'rgba(0, 0, 0, 0.3)',
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.75rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Tasks Completed Today:</span>
                <span className="mono" style={{ fontWeight: 600 }}>{state.tasks_completed_today}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Last Action:</span>
                <span className="mono">{state.last_task || 'None recorded'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Last Result:</span>
                <span className="mono" style={{ color: state.last_result?.includes('FAILED') ? 'var(--status-danger)' : 'var(--status-success)' }}>
                  {state.last_result || 'N/A'}
                </span>
              </div>
              {state.error_message && (
                <div style={{ color: 'var(--status-danger)', marginTop: '0.25rem', paddingTop: '0.25rem', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  Error: {state.error_message}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
