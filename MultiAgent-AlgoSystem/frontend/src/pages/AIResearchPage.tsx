import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  Cpu,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Plus,
  Lightbulb,
  ShieldAlert,
  Play,
  Check,
  X,
  Sliders,
  TrendingDown,
  Layers,
  Activity
} from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';

interface AIResearchPageProps {
  onTrainRegime: (symbol: string) => Promise<any>;
}

export const AIResearchPage: React.FC<AIResearchPageProps> = ({ onTrainRegime }) => {
  const [training, setTraining] = useState(false);
  const [mlResult, setMlResult] = useState<any>(null);
  const [hypotheses, setHypotheses] = useState<any[]>([]);
  const [experiments, setExperiments] = useState<any[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<any>(null);
  const [degradationData, setDegradationData] = useState<any>(null);
  const [loadingData, setLoadingData] = useState(false);
  const [investigating, setInvestigating] = useState(false);
  const [showNewModal, setShowNewModal] = useState(false);
  const [reviewComment, setReviewComment] = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  // New hypothesis form state
  const [newTitle, setNewTitle] = useState('');
  const [newStatement, setNewStatement] = useState('');
  const [newReasoning, setNewReasoning] = useState('');
  const [newTestPlan, setNewTestPlan] = useState('');
  const [newSuccessMetric, setNewSuccessMetric] = useState('');
  const [newFailureCondition, setNewFailureCondition] = useState('');

  const fetchResearchData = async () => {
    setLoadingData(true);
    try {
      const [hypRes, expRes, degRes] = await Promise.all([
        fetch('/api/research/hypotheses').catch(() => fetch('/api/v1/research/hypotheses')),
        fetch('/api/research/experiments').catch(() => fetch('/api/v1/research/experiments')),
        fetch('/api/performance/degradation').catch(() => fetch('/api/v1/performance/degradation')),
      ]);

      if (hypRes && hypRes.ok) {
        const data = await hypRes.json();
        setHypotheses(Array.isArray(data) ? data : []);
      }
      if (expRes && expRes.ok) {
        const data = await expRes.json();
        const expList = Array.isArray(data) ? data : [];
        setExperiments(expList);
        if (expList.length > 0) {
          setSelectedExperiment((prev: any) => {
            if (!prev) return expList[0];
            const updated = expList.find((e: any) => e.experiment_id === prev.experiment_id);
            return updated || expList[0];
          });
        }
      }
      if (degRes && degRes.ok) {
        const degData = await degRes.json();
        setDegradationData(degData);
      }
    } catch (e) {
      console.error('Failed to fetch research telemetry:', e);
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    fetchResearchData();
    const interval = setInterval(fetchResearchData, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerInvestigation = async () => {
    setInvestigating(true);
    try {
      const res = await fetch('/api/orchestrator/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          strategy_id: 'strategy_v1',
          symbol: 'EURUSD',
          issue: degradationData?.degradation_alerts?.[0]?.issue || 'Performance degradation check',
          force_run: true,
        }),
      });
      if (res.ok) {
        await fetchResearchData();
      }
    } catch (e) {
      console.error('Failed to trigger autonomous investigation:', e);
    } finally {
      setInvestigating(false);
    }
  };

  const handleReviewExperiment = async (decision: 'APPROVED_FOR_DEMO' | 'REJECTED') => {
    if (!selectedExperiment) return;
    setReviewSubmitting(true);
    try {
      const res = await fetch(`/api/research/experiments/${selectedExperiment.experiment_id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          operator_comment: reviewComment || `Human operator action: ${decision}`,
        }),
      });
      if (res.ok) {
        setReviewComment('');
        await fetchResearchData();
      }
    } catch (e) {
      console.error('Failed to record experiment review:', e);
    } finally {
      setReviewSubmitting(false);
    }
  };

  const handleTrain = async () => {
    setTraining(true);
    try {
      const res = await onTrainRegime('EURUSD');
      setMlResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setTraining(false);
    }
  };

  const handleCreateHypothesis = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/v1/research/hypotheses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newTitle,
          hypothesis_statement: newStatement,
          reasoning: newReasoning,
          test_plan: newTestPlan,
          success_metric: newSuccessMetric,
          failure_condition: newFailureCondition,
        }),
      });
      if (res.ok) {
        setShowNewModal(false);
        setNewTitle('');
        setNewStatement('');
        setNewReasoning('');
        setNewTestPlan('');
        setNewSuccessMetric('');
        setNewFailureCondition('');
        fetchResearchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const sampleStatus = degradationData?.sample_status || {
    status: 'INSUFFICIENT SAMPLE',
    trade_count: degradationData?.trade_count || 10,
    confidence: 'LOW',
    recommendation: 'Collect more empirical trade data before drawing structural conclusions.',
    thresholds: { insufficient: 30, early_analysis: 100 },
  };

  const alerts = degradationData?.degradation_alerts || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. Header Banner & Autonomous Investigation Trigger */}
      <div
        className="glass-panel"
        style={{
          borderLeft: '4px solid var(--accent-primary)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>
              Autonomous Research & Strategy Improvement Pipeline
            </h2>
            <span
              className="badge"
              style={{
                background:
                  sampleStatus.status === 'RESEARCHABLE'
                    ? 'rgba(16, 185, 129, 0.15)'
                    : sampleStatus.status === 'EARLY ANALYSIS'
                    ? 'rgba(14, 165, 233, 0.15)'
                    : 'rgba(245, 158, 11, 0.15)',
                color:
                  sampleStatus.status === 'RESEARCHABLE'
                    ? 'var(--accent-green, #10b981)'
                    : sampleStatus.status === 'EARLY ANALYSIS'
                    ? 'var(--accent-primary, #0ea5e9)'
                    : 'var(--accent-amber, #f59e0b)',
                border: '1px solid currentColor',
                fontWeight: 700,
                fontSize: '0.72rem',
              }}
            >
              SAMPLE: {sampleStatus.status} ({sampleStatus.trade_count || 10} trades)
            </span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
            Performance Agent continuously audits closed trades. When degradation is detected, Orchestrator activates
            Research & AI/ML to formulate testable hypotheses, generate bounded candidates, and run walk-forward backtests.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            onClick={handleTriggerInvestigation}
            disabled={investigating}
            className="btn btn-primary btn-sm"
            style={{ fontWeight: 700 }}
          >
            {investigating ? <RefreshCw className="animate-spin" size={14} /> : <Play size={14} />}
            <span>{investigating ? 'Running 11-Agent Investigation...' : 'Dispatch Autonomous Investigation'}</span>
          </button>
          <button onClick={() => setShowNewModal(true)} className="btn btn-secondary btn-sm">
            <Plus size={14} />
            <span>New Hypothesis</span>
          </button>
        </div>
      </div>

      {/* 2. Sample-Size Guardrails & Degradation Alerts Telemetry */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }}>
        {/* Sample-Size Guardrails Card */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>
              SAMPLE-SIZE GOVERNANCE
            </span>
            <span className="mono badge badge-neutral" style={{ fontSize: '0.7rem' }}>
              Confidence: {sampleStatus.confidence}
            </span>
          </div>

          <div
            style={{
              background: 'rgba(0, 0, 0, 0.25)',
              padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.78rem',
            }}
          >
            <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: '0.35rem' }}>
              Sample Status: {sampleStatus.status}
            </div>
            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              {sampleStatus.recommendation}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', fontSize: '0.72rem' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.5rem', borderRadius: '4px' }}>
              <div style={{ color: 'var(--text-muted)' }}>&lt; 30 Trades</div>
              <div style={{ fontWeight: 600, color: 'var(--accent-amber, #f59e0b)' }}>Insufficient</div>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.5rem', borderRadius: '4px' }}>
              <div style={{ color: 'var(--text-muted)' }}>30-100 Trades</div>
              <div style={{ fontWeight: 600, color: 'var(--accent-primary, #0ea5e9)' }}>Early Analysis</div>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.5rem', borderRadius: '4px' }}>
              <div style={{ color: 'var(--text-muted)' }}>100+ Trades</div>
              <div style={{ fontWeight: 600, color: 'var(--accent-green, #10b981)' }}>Researchable</div>
            </div>
          </div>
        </div>

        {/* Live Degradation Alerts */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldAlert size={16} color="var(--accent-amber, #f59e0b)" />
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                PERFORMANCE DEGRADATION MONITOR (EURUSD / PORTFOLIO)
              </span>
            </div>
            <span className="mono badge badge-amber" style={{ fontSize: '0.68rem' }}>
              {alerts.length} Flagged Pattern{alerts.length === 1 ? '' : 's'}
            </span>
          </div>

          {alerts.length > 0 ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.6rem' }}>
              {alerts.map((alt: any, idx: number) => (
                <div
                  key={idx}
                  style={{
                    background: 'rgba(245, 158, 11, 0.04)',
                    border: '1px solid rgba(245, 158, 11, 0.25)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.65rem 0.8rem',
                    fontSize: '0.75rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span style={{ fontWeight: 700, color: 'var(--accent-amber, #f59e0b)', textTransform: 'uppercase' }}>
                      {alt.issue}
                    </span>
                    <span className="mono" style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      Severity: {alt.severity}
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-secondary)', marginBottom: '0.3rem', fontSize: '0.73rem' }}>
                    {alt.reason}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.68rem' }}>
                    <span>Segment: {alt.segment_type} ({alt.segment_value})</span>
                    <span>Action: {alt.recommended_action}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              No critical performance degradation patterns detected. Expectancy and profit factor nominal.
            </div>
          )}
        </div>
      </div>

      {/* 3. Baseline vs Candidate Comparative Matrix & Robustness */}
      {selectedExperiment && selectedExperiment.metrics && (
        <div className="glass-panel" style={{ border: '1px solid var(--accent-cyan)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
                <span className="mono" style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                  {selectedExperiment.experiment_id}
                </span>
                <span style={{ fontSize: '0.95rem', fontWeight: 700 }}>
                  BASELINE: {selectedExperiment.baseline_strategy || 'strategy_v1'} vs CANDIDATE: {selectedExperiment.candidate_strategy || 'strategy_v1.1'}
                </span>
                <span className={`badge ${selectedExperiment.human_approved ? 'badge-green' : 'badge-amber'}`}>
                  {selectedExperiment.status}
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>
                Walk-Forward Out-of-Sample Evaluation: Training ({selectedExperiment.training_period}) | Validation ({selectedExperiment.validation_period})
              </p>
            </div>

            {/* Operator Review Controls */}
            {!selectedExperiment.human_approved ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <input
                  type="text"
                  placeholder="Operator audit comment..."
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  style={{
                    padding: '0.35rem 0.6rem',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(0, 0, 0, 0.4)',
                    border: '1px solid var(--border-subtle)',
                    color: '#fff',
                    fontSize: '0.75rem',
                    width: '200px',
                  }}
                />
                <button
                  onClick={() => handleReviewExperiment('APPROVED_FOR_DEMO')}
                  disabled={reviewSubmitting}
                  className="btn btn-primary btn-sm"
                  style={{ background: '#10b981', borderColor: '#10b981', color: '#fff', fontWeight: 700 }}
                  title="Approve candidate for forward paper/demo testing only. Live trading remains locked."
                >
                  <Check size={14} />
                  <span>Approve for Demo</span>
                </button>
                <button
                  onClick={() => handleReviewExperiment('REJECTED')}
                  disabled={reviewSubmitting}
                  className="btn btn-secondary btn-sm"
                  style={{ color: '#ef4444' }}
                >
                  <X size={14} />
                  <span>Reject</span>
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontSize: '0.8rem', fontWeight: 700 }}>
                <CheckCircle size={16} />
                <span>Approved for Demo Testing (Live Locked)</span>
              </div>
            )}
          </div>

          {/* Comparative Table */}
          <div style={{ overflowX: 'auto', marginBottom: '1rem' }}>
            <table className="data-table" style={{ width: '100%', fontSize: '0.8rem' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>METRIC</th>
                  <th style={{ textAlign: 'center', color: 'var(--text-muted)' }}>BASELINE (strategy_v1)</th>
                  <th style={{ textAlign: 'center', color: 'var(--accent-cyan)' }}>CANDIDATE ({selectedExperiment.candidate_strategy})</th>
                  <th style={{ textAlign: 'center' }}>DELTA</th>
                  <th style={{ textAlign: 'left' }}>CONCLUSION / IMPACT</th>
                </tr>
              </thead>
              <tbody>
                {selectedExperiment.metrics.map((row: any, idx: number) => {
                  const isImproved =
                    row.metric.includes('Drawdown') || row.metric.includes('Monte Carlo')
                      ? row.delta < 0
                      : row.delta > 0;
                  return (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{row.metric}</td>
                      <td className="mono" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                        {typeof row.baseline === 'number' ? row.baseline.toFixed(2) : String(row.baseline)}
                      </td>
                      <td className="mono" style={{ textAlign: 'center', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                        {typeof row.candidate === 'number' ? row.candidate.toFixed(2) : String(row.candidate)}
                      </td>
                      <td
                        className="mono"
                        style={{
                          textAlign: 'center',
                          fontWeight: 700,
                          color: row.delta === 0 ? 'var(--text-muted)' : isImproved ? '#10b981' : '#ef4444',
                        }}
                      >
                        {typeof row.delta === 'number' ? (row.delta > 0 ? `+${row.delta.toFixed(2)}` : row.delta.toFixed(2)) : 'N/A'}
                      </td>
                      <td style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {row.metric === 'Profit Factor' && 'Evaluates risk-adjusted gross win vs loss ratio'}
                        {row.metric === 'Expectancy ($)' && 'Expected monetary gain per executed order'}
                        {row.metric.includes('Drawdown') && 'Peak-to-trough capital preservation'}
                        {row.metric === 'Monte Carlo 95% DD (%)' && '95th percentile trade sequence stress permutation'}
                        {row.metric === 'Stability Score (0-1)' && 'Consistency of trade return distribution'}
                        {row.metric === 'OOS Return (%)' && 'Out-of-sample unseen validation bars'}
                        {row.metric === 'Win Rate (%)' && 'Percentage of winning trades'}
                        {row.metric === 'Trade Count' && 'Sample size of executed signals'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Candidate Parameters & Robustness Details */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1rem' }}>
            <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '0.4rem' }}>
                <Sliders size={14} />
                <span>CANDIDATE BOUNDED PARAMETERS</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.4rem' }}>
                {selectedExperiment.parameters &&
                  Object.entries(selectedExperiment.parameters).map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '2px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>{k}:</span>
                      <span className="mono" style={{ color: '#fff' }}>{String(v)}</span>
                    </div>
                  ))}
              </div>
            </div>

            <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem' }}>
              <div style={{ fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                EXPERIMENT GOVERNANCE AUDIT
              </div>
              <div style={{ color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: '0.4rem' }}>
                {selectedExperiment.conclusion}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '0.4rem' }}>
                Action Status: {selectedExperiment.action}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Split Layout: Hypotheses & Experiments Registry | AI/ML Console */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '1.5rem' }}>
        {/* Left Column: Hypotheses & Experiment Registry */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Falsifiable Hypotheses List */}
          <div className="glass-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Lightbulb size={18} color="var(--accent-primary)" />
                <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Falsifiable Market Hypotheses</h3>
              </div>
              <span className="mono badge badge-neutral" style={{ fontSize: '0.6875rem' }}>
                {hypotheses.length} Recorded
              </span>
            </div>

            {hypotheses.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {hypotheses.map((h) => (
                  <div
                    key={h.hypothesis_id}
                    style={{
                      background: 'rgba(0, 0, 0, 0.25)',
                      padding: '0.85rem',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                      <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', fontWeight: 700 }}>
                        {h.hypothesis_id}: {h.title}
                      </span>
                      <StatusBadge status={h.status} />
                    </div>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                      {h.hypothesis_statement}
                    </p>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                      <div><strong>Reasoning:</strong> {h.reasoning}</div>
                      <div><strong>Success Metric:</strong> {h.success_metric}</div>
                      <div><strong>Failure Condition:</strong> {h.failure_condition}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                No active hypotheses logged. Click "Dispatch Autonomous Investigation" to generate from degradation.
              </div>
            )}
          </div>

          {/* Experiments Registry */}
          <div className="glass-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <FlaskConical size={18} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>
                  Experiment Registry (Supabase experiments table)
                </h3>
              </div>
              <span className="mono badge badge-neutral" style={{ fontSize: '0.6875rem' }}>
                {experiments.length} Runs
              </span>
            </div>

            {experiments.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {experiments.map((exp) => (
                  <div
                    key={exp.experiment_id}
                    onClick={() => setSelectedExperiment(exp)}
                    style={{
                      background: selectedExperiment?.experiment_id === exp.experiment_id ? 'rgba(14, 165, 233, 0.1)' : 'rgba(0, 0, 0, 0.25)',
                      padding: '0.85rem',
                      borderRadius: 'var(--radius-sm)',
                      border: selectedExperiment?.experiment_id === exp.experiment_id ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                      <span className="mono" style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
                        {exp.experiment_id} (Hypothesis: {exp.hypothesis_id})
                      </span>
                      <span className={`badge ${exp.human_approved ? 'badge-green' : 'badge-amber'}`}>
                        {exp.human_approved ? 'Approved for Demo' : 'Pending Human Review'}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                      Baseline: {exp.baseline_strategy || 'strategy_v1'} &rarr; Candidate: {exp.candidate_strategy || 'strategy_v1.1'} | Dataset: {exp.dataset || exp.dataset_period}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-primary)' }}>
                      <strong>Audit:</strong> {exp.conclusion || exp.action}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                No experiments recorded yet. Dispatch an investigation to test candidate strategies.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: AI/ML Feature & Regime Classifier Console */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <Cpu color="var(--accent-primary)" size={20} />
              <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>AI / ML Agent Feature & Regime Explorer</h3>
            </div>
            <p style={{ fontSize: '0.78125rem', color: 'var(--text-secondary)' }}>
              Trains a Random Forest classifier over leak-free return & volatility features using 3-fold Walk-Forward TimeSeriesSplit cross-validation.
            </p>
          </div>

          <div
            style={{
              background: 'rgba(0, 0, 0, 0.25)',
              padding: '0.85rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.75rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.4rem',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Engineered Features:</span>
              <span className="mono">8 Leak-Free Lagged Indicators</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Validation Technique:</span>
              <span className="mono">TimeSeriesSplit (Strictly No Lookahead)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Regime Classes:</span>
              <span>TREND_UP, TREND_DOWN, RANGE, HIGH_VOL</span>
            </div>
          </div>

          <button
            onClick={handleTrain}
            disabled={training}
            className="btn btn-primary"
            style={{ width: '100%', fontWeight: 700 }}
          >
            {training ? <RefreshCw className="animate-spin" size={16} /> : <Cpu size={16} />}
            <span>Train Regime Classifier (TimeSeriesSplit)</span>
          </button>

          {mlResult && (
            <div
              style={{
                background: 'rgba(14, 165, 233, 0.08)',
                border: '1px solid rgba(14, 165, 233, 0.25)',
                padding: '0.85rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8125rem',
              }}
            >
              <div style={{ fontWeight: 600, color: 'var(--accent-primary)', marginBottom: '0.4rem' }}>
                Walk-Forward Cross-Validation Telemetry
              </div>
              <div>
                Average CV Accuracy:{' '}
                <span className="mono" style={{ fontWeight: 600 }}>
                  {(mlResult.average_cv_accuracy * 100).toFixed(1)}%
                </span>
              </div>
              <div style={{ fontSize: '0.71875rem', color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
                Fold Accuracies: {mlResult.cv_scores?.map((s: number) => `${(s * 100).toFixed(1)}%`).join(' | ')}
              </div>
              <div style={{ fontSize: '0.71875rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
                Model: {mlResult.model_type} ({mlResult.total_samples} samples)
              </div>
            </div>
          )}
        </div>
      </div>

      {/* New Hypothesis Modal */}
      {showNewModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={() => setShowNewModal(false)}
        >
          <div
            className="glass-panel"
            style={{ width: '100%', maxWidth: '500px', backgroundColor: 'var(--bg-surface-elevated)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
              Formulate Falsifiable Hypothesis
            </h3>
            <form onSubmit={handleCreateHypothesis} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Hypothesis Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Volatility Filter stops premature hits"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.45rem',
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    color: '#fff',
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Hypothesis Statement (Testable)</label>
                <textarea
                  required
                  placeholder="Strategy performance may deteriorate during elevated volatility regimes..."
                  value={newStatement}
                  onChange={(e) => setNewStatement(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.45rem',
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    color: '#fff',
                    minHeight: '60px',
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Reasoning / Root Cause</label>
                <input
                  type="text"
                  placeholder="Elevated spread and wide bars trigger ATR stops prematurely"
                  value={newReasoning}
                  onChange={(e) => setNewReasoning(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.45rem',
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    color: '#fff',
                  }}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Success Metric</label>
                  <input
                    type="text"
                    placeholder="Profit Factor > 1.2"
                    value={newSuccessMetric}
                    onChange={(e) => setNewSuccessMetric(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.45rem',
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      color: '#fff',
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Failure Condition</label>
                  <input
                    type="text"
                    placeholder="Expectancy remains < 0"
                    value={newFailureCondition}
                    onChange={(e) => setNewFailureCondition(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.45rem',
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      color: '#fff',
                    }}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button type="button" onClick={() => setShowNewModal(false)} className="btn btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Save Hypothesis
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
