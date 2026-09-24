import React, { useState, useEffect } from 'react';
import {
  Brain,
  Cpu,
  ShieldCheck,
  Zap,
  Activity,
  AlertTriangle,
  Play,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Clock,
  Terminal,
  FileText,
  Search,
  ChevronRight,
  Database,
  Radio,
  Sliders,
  Sparkles,
  ShieldAlert,
  Layers,
  FlaskConical,
  Eye,
  GitBranch,
} from 'lucide-react';

interface AgentControlCenterPageProps {
  agents?: any[];
  onRefresh?: () => void;
}

export const AgentControlCenterPage: React.FC<AgentControlCenterPageProps> = () => {
  const [aiStatus, setAiStatus] = useState<any>({
    status: 'IDLE',
    current_task: 'Monitoring markets & waiting for triggers',
    current_tool: null,
    current_run: null,
    current_run_id: null,
    last_action: 'Initialized AI Trading & Research Agent',
    last_decision: 'System ready for quantitative research and analysis',
    last_result: 'System ready for quantitative research and analysis',
    last_error: null,
    last_heartbeat: new Date().toISOString(),
    last_latency_ms: 120.5,
    model: 'gpt-4o-mini',
    has_openai_key: false,
    trading_mode: 'DEMO',
  });

  const [servicesHealth, setServicesHealth] = useState<any>({
    status: 'OPERATIONAL',
    database: { status: 'CONNECTED', engine: 'PostgreSQL (Supabase)' },
    supabase: { status: 'CONNECTED', engine: 'PostgreSQL (Supabase)' },
    mt5: { connected: true, gateway_mode: 'DEMO', equity: 10000.0, balance: 10000.0, account: 'DEMO' },
    ai_runtime: { status: 'IDLE', model: 'gpt-4o-mini' },
    risk_engine: { active: true, kill_switch_active: false, consecutive_losses: 0 },
    execution_engine: { status: 'OPERATIONAL', mode: 'DEMO ONLY', max_order_lots: 0.5 },
    backtest_engine: { status: 'OPERATIONAL', capabilities: ['Monte Carlo (95% DD)', 'Walk-Forward OOS'] },
    supervisor: { status: 'RUNNING', last_heartbeat: new Date().toISOString(), events_detected_count: 0 },
    kill_switch: { active: false, reason: null, operator: null },
  });

  const [riskStatus, setRiskStatus] = useState<any>({
    kill_switch_active: false,
    current_drawdown_pct: 0.0,
    daily_loss_pct: 0.0,
    open_positions_count: 0,
    consecutive_losses: 0,
    trading_mode: 'DEMO',
    limits: {
      risk_per_trade_pct: 1.0,
      max_daily_loss_pct: 3.0,
      max_portfolio_drawdown_pct: 10.0,
      max_open_positions: 5,
      max_symbol_exposure: 2,
    },
  });

  const [aiRuns, setAiRuns] = useState<any[]>([]);
  const [toolCalls, setToolCalls] = useState<any[]>([]);
  const [experiments, setExperiments] = useState<any[]>([]);
  const [hypotheses, setHypotheses] = useState<any[]>([]);
  const [candidates, setCandidates] = useState<any[]>([]);
  const [selectedRun, setSelectedRun] = useState<any>(null);
  const [isRunningTask, setIsRunningTask] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [realtimeEvents, setRealtimeEvents] = useState<any[]>([]);
  const [sseConnected, setSseConnected] = useState(false);

  // Fetch telemetry & configure SSE real-time connection
  useEffect(() => {
    fetchTelemetry();

    // 1. Server-Sent Events (SSE) Stream for real-time zero-lag updates
    let es: EventSource | null = null;
    try {
      es = new EventSource('/api/v1/stream');
      es.onopen = () => setSseConnected(true);
      es.onerror = () => setSseConnected(false);
      es.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.type === 'BUS_EVENT') {
            setRealtimeEvents((prev) => [payload, ...prev.slice(0, 49)]);
            // Auto refresh telemetry if critical event received
            if (['ORDER_EXECUTED', 'TRADE_DETECTED', 'TRADE_CLOSED', 'AI_TOOL_CALL', 'RESEARCH_STARTED'].includes(payload.event_type)) {
              fetchTelemetry();
            }
          }
        } catch (_) {}
      };
    } catch (_) {
      setSseConnected(false);
    }

    // 2. Fallback polling interval every 3.5s
    const interval = setInterval(fetchTelemetry, 3500);

    return () => {
      clearInterval(interval);
      if (es) es.close();
    };
  }, []);

  const fetchTelemetry = async () => {
    try {
      // 1. AI Agent status
      const statusRes = await fetch('/api/ai/status');
      if (statusRes.ok) {
        const data = await statusRes.json();
        setAiStatus(data);
      }

      // 2. System services health
      const healthRes = await fetch('/api/system/health');
      if (healthRes.ok) {
        const data = await healthRes.json();
        setServicesHealth(data);
      }

      // 3. Risk status
      const riskRes = await fetch('/api/risk/status');
      if (riskRes.ok) {
        const data = await riskRes.json();
        setRiskStatus(data);
      }

      // 4. AI Runs
      const runsRes = await fetch('/api/ai/runs?limit=10');
      if (runsRes.ok) {
        const data = await runsRes.json();
        if (Array.isArray(data)) setAiRuns(data);
      }

      // 5. AI Tool Calls
      const toolsRes = await fetch('/api/ai/tool-calls?limit=15');
      if (toolsRes.ok) {
        const data = await toolsRes.json();
        if (Array.isArray(data)) setToolCalls(data);
      }

      // 6. Research Experiments
      const expRes = await fetch('/api/research/experiments?limit=10');
      if (expRes.ok) {
        const data = await expRes.json();
        if (Array.isArray(data)) setExperiments(data);
      }

      // 7. Research Hypotheses
      const hypRes = await fetch('/api/v1/research/hypotheses');
      if (hypRes.ok) {
        const data = await hypRes.json();
        if (Array.isArray(data)) setHypotheses(data);
      }

      // 8. Candidate Strategy Versions
      const candRes = await fetch('/api/v1/strategies/versions');
      if (candRes.ok) {
        const data = await candRes.json();
        if (Array.isArray(data)) setCandidates(data);
      }
    } catch (_) {}
  };

  const handleTriggerAnalysis = async () => {
    setIsRunningTask(true);
    try {
      await fetch('/api/ai/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy_id: 'strategy_v1', symbol: 'EURUSD' }),
      });
      await fetchTelemetry();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunningTask(false);
    }
  };

  const handleTriggerResearch = async () => {
    setIsRunningTask(true);
    try {
      await fetch('/api/ai/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: 'High Spread Degradation and Walk-Forward Stability',
          strategy_id: 'strategy_v1',
        }),
      });
      await fetchTelemetry();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunningTask(false);
    }
  };

  const handleCustomPromptSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customPrompt.trim() || isRunningTask) return;
    setIsRunningTask(true);
    try {
      await fetch('/api/ai/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_name: 'Operator Query',
          prompt: customPrompt,
        }),
      });
      setCustomPrompt('');
      await fetchTelemetry();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunningTask(false);
    }
  };

  // Status badge styling helper
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'IDLE':
        return { bg: 'rgba(16, 185, 129, 0.12)', text: '#10b981', border: 'rgba(16, 185, 129, 0.3)' };
      case 'THINKING':
      case 'RESEARCHING':
      case 'BACKTESTING':
        return { bg: 'rgba(14, 165, 233, 0.15)', text: '#38bdf8', border: 'rgba(14, 165, 233, 0.4)' };
      case 'RISK_CHECK':
      case 'EXECUTING':
        return { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24', border: 'rgba(245, 158, 11, 0.4)' };
      case 'WAITING_APPROVAL':
        return { bg: 'rgba(99, 102, 241, 0.15)', text: '#818cf8', border: 'rgba(99, 102, 241, 0.4)' };
      case 'ERROR':
        return { bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', border: 'rgba(239, 68, 68, 0.4)' };
      default:
        return { bg: 'rgba(148, 163, 184, 0.12)', text: '#94a3b8', border: 'rgba(148, 163, 184, 0.2)' };
    }
  };

  const statusStyle = getStatusColor(aiStatus.status);

  // Group experiments
  const activeExps = experiments.filter((e) => e.status === 'RUNNING' || e.status === 'PROPOSED');
  const completedExps = experiments.filter((e) => e.status === 'COMPLETED' || e.status === 'APPROVED_FOR_DEMO');
  const pendingReviewExps = experiments.filter((e) => e.status === 'PENDING_HUMAN_REVIEW');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* ========================================================================= */}
      {/* 1. AI TRADING AGENT PRIMARY COCKPIT */}
      {/* ========================================================================= */}
      <div
        className="glass-panel"
        style={{
          padding: '1.75rem',
          border: '1px solid rgba(14, 165, 233, 0.2)',
          background: 'linear-gradient(180deg, rgba(15, 21, 35, 0.95) 0%, rgba(10, 14, 24, 0.95) 100%)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
              <div
                style={{
                  background: 'rgba(14, 165, 233, 0.15)',
                  padding: '0.5rem',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Brain size={26} color="var(--accent-primary)" />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <h2 style={{ fontSize: '1.375rem', fontWeight: 700, letterSpacing: '-0.01em' }}>
                    AI TRADING & RESEARCH AGENT
                  </h2>
                  <span
                    style={{
                      background: 'rgba(14, 165, 233, 0.1)',
                      color: 'var(--accent-primary)',
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      padding: '0.15rem 0.5rem',
                      borderRadius: 'var(--radius-full)',
                      border: '1px solid rgba(14, 165, 233, 0.25)',
                    }}
                  >
                    OpenAI Agents SDK
                  </span>
                  <span
                    style={{
                      background: 'rgba(245, 158, 11, 0.1)',
                      color: '#fbbf24',
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      padding: '0.15rem 0.5rem',
                      borderRadius: 'var(--radius-full)',
                      border: '1px solid rgba(245, 158, 11, 0.25)',
                    }}
                  >
                    DEMO ONLY
                  </span>
                  {sseConnected && (
                    <span
                      style={{
                        background: 'rgba(16, 185, 129, 0.1)',
                        color: '#10b981',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        padding: '0.15rem 0.5rem',
                        borderRadius: 'var(--radius-full)',
                        border: '1px solid rgba(16, 185, 129, 0.25)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      <Radio size={12} className="pulse-dot" /> SSE LIVE
                    </span>
                  )}
                </div>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                  Autonomous reasoning engine executing controlled market analysis, statistical attribution, backtesting, and gated trade proposals.
                </p>
              </div>
            </div>
          </div>

          {/* Runtime State Badge & Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.4rem 0.85rem',
                borderRadius: 'var(--radius-full)',
                background: statusStyle.bg,
                border: `1px solid ${statusStyle.border}`,
                color: statusStyle.text,
                fontWeight: 700,
                fontSize: '0.8125rem',
              }}
            >
              <span
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: statusStyle.text,
                  display: 'inline-block',
                }}
              />
              STATUS: {aiStatus.status}
            </div>

            <button
              onClick={handleTriggerAnalysis}
              disabled={isRunningTask}
              className="btn btn-sm btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Activity size={14} />
              Run Analysis
            </button>

            <button
              onClick={handleTriggerResearch}
              disabled={isRunningTask}
              className="btn btn-sm btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Sparkles size={14} />
              Run Research
            </button>
          </div>
        </div>

        {/* Real AI Panel: Status, Current Task, Current Tool, Current Run, Last Action, Last Result, Last Error */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            padding: '1.25rem',
            background: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Current Task
            </span>
            <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
              {aiStatus.current_task || 'Idle — Standing by'}
            </p>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Current Tool
            </span>
            <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--accent-primary)', marginTop: '0.2rem' }} className="mono">
              {aiStatus.current_tool ? `${aiStatus.current_tool}()` : 'None (No active tool call)'}
            </p>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Current Run
            </span>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }} className="mono">
              {aiStatus.current_run || aiStatus.current_run_id || 'None'}
            </p>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Last Action
            </span>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              {aiStatus.last_action || 'System initialized'}
            </p>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Last Result
            </span>
            <p style={{ fontSize: '0.8125rem', color: '#10b981', marginTop: '0.2rem', fontWeight: 500 }}>
              {aiStatus.last_result || aiStatus.last_decision || 'Standing by'}
            </p>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Last Error
            </span>
            <p style={{ fontSize: '0.8125rem', color: aiStatus.last_error ? '#f87171' : 'var(--text-muted)', marginTop: '0.2rem' }} className="mono">
              {aiStatus.last_error || 'None (Healthy)'}
            </p>
          </div>
        </div>

        {/* Ad-hoc Query Box */}
        <form onSubmit={handleCustomPromptSubmit} style={{ marginTop: '1.25rem', display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            placeholder="Ask AI Agent to investigate trades, analyze drawdowns, run walk-forward, or test a hypothesis..."
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            disabled={isRunningTask}
            style={{
              flex: 1,
              padding: '0.6rem 1rem',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-medium)',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
            }}
          />
          <button
            type="submit"
            disabled={isRunningTask || !customPrompt.trim()}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', whiteSpace: 'nowrap' }}
          >
            <Play size={14} />
            {isRunningTask ? 'Executing...' : 'Submit Prompt'}
          </button>
        </form>
      </div>

      {/* ========================================================================= */}
      {/* 2. DETERMINISTIC SYSTEM SERVICES (ALL 8 ARCHITECTURAL COMPONENTS) */}
      {/* ========================================================================= */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.85rem' }}>
          <ShieldCheck size={18} color="var(--accent-primary)" />
          <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>DETERMINISTIC SYSTEM SERVICES</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            (Live telemetry across all 8 architectural services)
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
          {/* 1. MT5 Gateway */}
          <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>1. MT5 Gateway</span>
              <span style={{ fontSize: '0.7rem', color: servicesHealth.mt5?.connected ? '#10b981' : '#f87171', fontWeight: 700 }}>
                {servicesHealth.mt5?.connected ? 'CONNECTED' : 'DISCONNECTED'}
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }} className="mono">
              Mode: {servicesHealth.mt5?.gateway_mode || 'DEMO'} | Equity: ${Number(servicesHealth.mt5?.equity || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>

          {/* 2. Supabase DB */}
          <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>2. Supabase DB</span>
              <span style={{ fontSize: '0.7rem', color: servicesHealth.supabase?.status === 'CONNECTED' ? '#10b981' : '#f87171', fontWeight: 700 }}>
                {servicesHealth.supabase?.status || 'CONNECTED'}
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {servicesHealth.supabase?.engine || 'PostgreSQL (Supabase)'}
            </p>
          </div>

          {/* 3. AI Runtime */}
          <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>3. AI Runtime</span>
              <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 700 }}>
                {servicesHealth.ai_runtime?.status || aiStatus.status || 'IDLE'}
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              OpenAI Agents SDK | {servicesHealth.ai_runtime?.model || aiStatus.model}
            </p>
          </div>

          {/* 4. Risk Engine */}
          <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>4. Risk Engine</span>
              <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 700 }}>ACTIVE</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Max Risk 1% | Daily 3% | DD 10%
            </p>
          </div>

          {/* 5. Execution Engine */}
          <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>5. Execution Engine</span>
              <span style={{ fontSize: '0.7rem', color: servicesHealth.execution_engine?.status === 'OPERATIONAL' ? '#10b981' : '#f87171', fontWeight: 700 }}>
                {servicesHealth.execution_engine?.status || 'OPERATIONAL'}
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {servicesHealth.execution_engine?.mode || 'DEMO ONLY'} (Idempotent)
            </p>
          </div>

          {/* 6. Backtest Engine */}
          <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>6. Backtest Engine</span>
              <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 700 }}>OPERATIONAL</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Monte Carlo (95% DD) & Walk-Forward
            </p>
          </div>

          {/* 7. Supervisor */}
          <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>7. Supervisor</span>
              <span style={{ fontSize: '0.7rem', color: servicesHealth.supervisor?.status === 'RUNNING' ? '#10b981' : '#f87171', fontWeight: 700 }}>
                {servicesHealth.supervisor?.status || 'RUNNING'}
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Events: {servicesHealth.supervisor?.events_detected_count ?? 0} | Autonomous Runtime
            </p>
          </div>

          {/* 8. Kill Switch */}
          <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>8. Kill Switch</span>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  color: servicesHealth.kill_switch?.active || servicesHealth.risk_engine?.kill_switch_active ? '#ef4444' : '#10b981',
                }}
              >
                {servicesHealth.kill_switch?.active || servicesHealth.risk_engine?.kill_switch_active ? 'ENGAGED' : 'DISENGAGED'}
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Persistent Dual-Store (Disk + DB)
            </p>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. DETERMINISTIC RISK PANEL */}
      {/* ========================================================================= */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: 'var(--radius-md)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert size={18} color="var(--accent-primary)" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>DETERMINISTIC RISK PANEL</h3>
          </div>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '0.2rem 0.6rem',
              borderRadius: 'var(--radius-full)',
              background: riskStatus.kill_switch_active ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
              color: riskStatus.kill_switch_active ? '#f87171' : '#10b981',
            }}
          >
            KILL SWITCH: {riskStatus.kill_switch_active ? 'ENGAGED' : 'DISENGAGED'}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
          <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Risk / Trade</span>
            <p style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
              1.0%
            </p>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Fixed deterministic limit</span>
          </div>

          <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Daily Loss</span>
            <p style={{ fontSize: '1.125rem', fontWeight: 700, color: riskStatus.daily_loss_pct > 2.0 ? '#f87171' : '#10b981', marginTop: '0.2rem' }}>
              {Number(riskStatus.daily_loss_pct || 0).toFixed(2)}%
            </p>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Limit: 3.0% Max</span>
          </div>

          <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Drawdown</span>
            <p style={{ fontSize: '1.125rem', fontWeight: 700, color: riskStatus.current_drawdown_pct > 5.0 ? '#f87171' : '#10b981', marginTop: '0.2rem' }}>
              {Number(riskStatus.current_drawdown_pct || 0).toFixed(2)}%
            </p>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Limit: 10.0% Max</span>
          </div>

          <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Exposure</span>
            <p style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
              {riskStatus.open_positions_count || 0} / 2 Symbols
            </p>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Per-symbol ceiling</span>
          </div>

          <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Open Positions</span>
            <p style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
              {riskStatus.open_positions_count || 0} / 5 Max
            </p>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Max portfolio count</span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 4. AUTONOMOUS RESEARCH PANEL */}
      {/* ========================================================================= */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: 'var(--radius-md)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.2rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FlaskConical size={18} color="var(--accent-primary)" />
            <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>AUTONOMOUS RESEARCH PANEL</h4>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem' }}>
            <span style={{ color: '#38bdf8' }}>Hypotheses: {hypotheses.length}</span>
            <span style={{ color: '#818cf8' }}>Experiments: {experiments.length}</span>
            <span style={{ color: '#10b981' }}>Candidates: {candidates.length}</span>
            <span style={{ color: '#fbbf24' }}>Completed: {completedExps.length}</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {/* Hypotheses Column */}
          <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.6rem' }}>
              <GitBranch size={15} color="var(--accent-primary)" />
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Formulated Hypotheses</span>
            </div>
            {hypotheses.length === 0 ? (
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>No hypotheses formulated yet.</p>
            ) : (
              hypotheses.slice(0, 4).map((h, i) => (
                <div key={h.hypothesis_id || i} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '0.75rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>{h.hypothesis_id}: </span>
                  <span style={{ color: 'var(--text-primary)' }}>{h.title || h.description || 'Hypothesis'}</span>
                </div>
              ))
            )}
          </div>

          {/* Experiments Column */}
          <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.6rem' }}>
              <Layers size={15} color="#fbbf24" />
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Active & Completed Experiments</span>
            </div>
            {experiments.length === 0 ? (
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>No experiments executed yet.</p>
            ) : (
              experiments.slice(0, 4).map((exp, i) => (
                <div key={exp.experiment_id || i} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{exp.experiment_id}</span>
                    <span style={{ color: exp.status === 'COMPLETED' ? '#10b981' : '#38bdf8', fontWeight: 600 }}>{exp.status}</span>
                  </div>
                  <span style={{ color: 'var(--text-secondary)' }}>{exp.baseline_strategy} → {exp.candidate_strategy}</span>
                </div>
              ))
            )}
          </div>

          {/* Candidate Strategies Column */}
          <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.6rem' }}>
              <ShieldCheck size={15} color="#10b981" />
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Candidate Strategies (Human Gated)</span>
            </div>
            {candidates.length === 0 ? (
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>No candidates awaiting review.</p>
            ) : (
              candidates.slice(0, 4).map((c, i) => (
                <div key={c.version || i} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{c.strategy_id} v{c.version}</span>
                    <span style={{ color: c.status === 'ACTIVE' ? '#10b981' : '#818cf8', fontWeight: 600 }}>{c.status}</span>
                  </div>
                  <span style={{ color: 'var(--text-secondary)' }}>Requires human review before DEMO</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 5. RECENT RUNS & AUDITED TOOL CALLS */}
      {/* ========================================================================= */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.25rem' }}>
        {/* Recent AI Executions */}
        <div className="glass-panel" style={{ padding: '1.25rem', borderRadius: 'var(--radius-md)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Terminal size={17} color="var(--accent-primary)" />
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 600 }}>Recent AI Runs & Investigations</h4>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }} className="mono">
              {aiRuns.length} Audited
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', maxHeight: '360px', overflowY: 'auto' }}>
            {aiRuns.length === 0 ? (
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem' }}>
                No AI runs recorded yet. Click "Run Analysis" or "Run Research" above.
              </p>
            ) : (
              aiRuns.map((r, idx) => (
                <div
                  key={r.run_id || idx}
                  onClick={() => setSelectedRun(r)}
                  style={{
                    padding: '0.75rem',
                    background: selectedRun?.run_id === r.run_id ? 'rgba(14, 165, 233, 0.12)' : 'var(--bg-subtle)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {r.task}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 600 }} className="mono">
                      {r.latency_ms ? `${r.latency_ms}ms` : 'OK'}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.response || r.response_preview || 'Completed execution.'}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Real-Time Tool Calls Feed */}
        <div className="glass-panel" style={{ padding: '1.25rem', borderRadius: 'var(--radius-md)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Cpu size={17} color="#fbbf24" />
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 600 }}>Controlled Tool Calls</h4>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }} className="mono">
              Live Stream
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '360px', overflowY: 'auto' }}>
            {toolCalls.length === 0 ? (
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem' }}>
                No tool calls logged yet. Tools execute automatically during agent tasks.
              </p>
            ) : (
              toolCalls.map((tc, idx) => (
                <div
                  key={tc.tool_call_id || idx}
                  style={{
                    padding: '0.6rem 0.75rem',
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--accent-primary)' }} className="mono">
                      {tc.tool_name}()
                    </span>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {tc.output_preview ? tc.output_preview.slice(0, 70) : 'Success'}
                    </p>
                  </div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }} className="mono">
                    {tc.latency_ms ? `${tc.latency_ms}ms` : '—'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Selected Run Details Modal */}
      {selectedRun && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
          onClick={() => setSelectedRun(null)}
        >
          <div
            className="glass-panel"
            style={{
              maxWidth: '680px',
              width: '100%',
              maxHeight: '80vh',
              overflowY: 'auto',
              padding: '1.75rem',
              borderRadius: 'var(--radius-lg)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>{selectedRun.task}</h3>
              <button onClick={() => setSelectedRun(null)} className="btn btn-sm btn-secondary">
                Close
              </button>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }} className="mono">
              Run ID: {selectedRun.run_id} | Latency: {selectedRun.latency_ms}ms
            </p>
            <div
              style={{
                background: 'var(--bg-app)',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.8125rem',
                lineHeight: 1.6,
                color: 'var(--text-primary)',
                whiteSpace: 'pre-wrap',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {selectedRun.response || 'No output recorded.'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
