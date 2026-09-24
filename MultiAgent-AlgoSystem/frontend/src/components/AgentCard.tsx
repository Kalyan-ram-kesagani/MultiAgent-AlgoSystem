import React from 'react';
import {
  Brain,
  Database,
  Cpu,
  ShieldCheck,
  Zap,
  Activity,
  BookOpen,
  LineChart,
  GitBranch,
  Search,
  Eye,
  Clock,
  CheckCircle2,
  AlertTriangle,
  PlayCircle,
} from 'lucide-react';
import { StatusBadge } from './StatusBadge';

interface AgentCardProps {
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
  onClick: () => void;
}

const getAgentIcon = (role: string) => {
  switch (role) {
    case 'ORCHESTRATOR':
      return <Brain size={18} color="#0ea5e9" />;
    case 'RESEARCH':
      return <Search size={18} color="#a855f7" />;
    case 'DATA':
      return <Database size={18} color="#38bdf8" />;
    case 'STRATEGY':
      return <GitBranch size={18} color="#0ea5e9" />;
    case 'AI_ML':
      return <Cpu size={18} color="#818cf8" />;
    case 'BACKTEST':
      return <PlayCircle size={18} color="#f59e0b" />;
    case 'RISK':
      return <ShieldCheck size={18} color="#10b981" />;
    case 'EXECUTION':
      return <Zap size={18} color="#06b6d4" />;
    case 'MONITORING':
      return <Eye size={18} color="#14b8a6" />;
    case 'JOURNAL':
      return <BookOpen size={18} color="#6366f1" />;
    case 'PERFORMANCE':
      return <LineChart size={18} color="#ec4899" />;
    default:
      return <Activity size={18} color="#0ea5e9" />;
  }
};

const formatHeartbeat = (timestampStr?: string) => {
  if (!timestampStr) return 'Offline';
  try {
    const then = new Date(timestampStr).getTime();
    const now = Date.now();
    const sec = Math.max(0, Math.floor((now - then) / 1000));
    if (sec < 5) return 'Just now';
    if (sec < 60) return `${sec}s ago`;
    return `${Math.floor(sec / 60)}m ago`;
  } catch {
    return 'Active';
  }
};

export const AgentCard: React.FC<AgentCardProps> = ({ metadata, state, onClick }) => {
  const isAi = metadata.agent_type === 'AI_REASONING';
  const isWorking = state.status === 'WORKING';
  const isError = state.status === 'ERROR';

  return (
    <div
      onClick={onClick}
      className="glass-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.85rem',
        cursor: 'pointer',
        borderLeft: isWorking
          ? '3px solid var(--accent-primary)'
          : isError
          ? '3px solid var(--status-danger)'
          : '3px solid transparent',
        transition: 'all 0.15s ease',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div
            style={{
              padding: '0.45rem',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {getAgentIcon(metadata.role)}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{metadata.name}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.15rem' }}>
              <span className={`badge ${isAi ? 'badge-indigo' : 'badge-neutral'}`} style={{ fontSize: '0.625rem', padding: '0.1rem 0.4rem' }}>
                {isAi ? 'AI Reasoning' : 'Deterministic'}
              </span>
              <span className="mono" style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                v{metadata.version}
              </span>
            </div>
          </div>
        </div>
        <StatusBadge status={state.status} />
      </div>

      {/* Description */}
      <p style={{ fontSize: '0.78125rem', color: 'var(--text-secondary)', lineHeight: 1.4, minHeight: '2.2rem' }}>
        {metadata.description}
      </p>

      {/* Activity Status */}
      <div
        style={{
          background: 'rgba(0, 0, 0, 0.25)',
          padding: '0.6rem 0.75rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.75rem',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>
            {state.current_task ? 'Current Task:' : 'Last Action:'}
          </span>
          <span className="mono" style={{ color: state.current_task ? 'var(--accent-primary)' : 'var(--text-secondary)', fontWeight: 500 }}>
            {state.current_task || state.last_task || 'Awaiting task'}
          </span>
        </div>
        {state.last_result && !state.current_task && (
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            Result: {state.last_result}
          </div>
        )}
      </div>

      {/* Footer: Heartbeat and Tasks Today */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.71875rem',
          color: 'var(--text-muted)',
          paddingTop: '0.4rem',
          borderTop: '1px solid rgba(255, 255, 255, 0.04)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <span className={`pulse-dot ${state.status === 'ERROR' ? 'pulse-dot-red' : ''}`} />
          <span>Heartbeat: {formatHeartbeat(state.heartbeat_timestamp)}</span>
        </div>
        <div>
          <span>Tasks today: </span>
          <span className="mono" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
            {state.tasks_completed_today}
          </span>
        </div>
      </div>
    </div>
  );
};
