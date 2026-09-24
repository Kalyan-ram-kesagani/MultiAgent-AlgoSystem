import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { KillSwitchModal } from './components/KillSwitchModal';
import { OverviewPage } from './pages/OverviewPage';
import { AgentControlCenterPage } from './pages/AgentControlCenterPage';
import { LiveTradingPage } from './pages/LiveTradingPage';
import { StrategiesPage } from './pages/StrategiesPage';
import { BacktestingPage } from './pages/BacktestingPage';
import { RiskPage } from './pages/RiskPage';
import { JournalPage } from './pages/JournalPage';
import { AIResearchPage } from './pages/AIResearchPage';
import { MonitoringPage } from './pages/MonitoringPage';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [killModalOpen, setKillModalOpen] = useState(false);
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [agents, setAgents] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);


  // Core state synced strictly with backend (no hardcoded fake values)
  const [systemStatus, setSystemStatus] = useState<any>({
    environment: 'UNKNOWN',
    status: 'CONNECTING...',
    api_online: false,
    database_connected: false,
    mt5_connected: false,
    is_simulation: false,
    gateway_mode: 'DISCONNECTED',
  });

  const [account, setAccount] = useState<any>({
    login: null,
    server: null,
    balance: null,
    equity: null,
    leverage: null,
    trade_mode: null,
  });

  const [circuitBreaker, setCircuitBreaker] = useState<any>({
    kill_switch_active: false,
    pause_reason: null,
    consecutive_losses: 0,
    current_day_loss: 0.0,
    current_drawdown_pct: 0.0,
    max_drawdown_threshold_pct: 10.0,
    max_daily_loss_threshold_pct: 3.0,
  });

  const [strategies, setStrategies] = useState<any[]>([
    {
      strategy_id: 'strategy_v1',
      version: '1.0.0',
      name: 'Trend Pullback Confirmation',
      description: 'Deterministic trend-following pullback strategy using EMA, ATR, and RSI filters.',
      timeframe: 'H1',
      supported_symbols: ['EURUSD', 'XAUUSD', 'GBPUSD'],
      default_parameters: {
        ema_fast: 20,
        ema_slow: 50,
        atr_period: 14,
        rsi_period: 14,
        swing_lookback: 5,
        atr_stop_multiplier: 1.5,
        reward_risk_ratio: 2.0,
        min_stop_distance: 0.001,
      },
    },
  ]);
  const [trades, setTrades] = useState<any[]>([]);
  const [performance, setPerformance] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);

  // Fetch initial telemetry, catalog, and trade journal
  useEffect(() => {
    fetchAll();

    // Real-Time Server-Sent Events (SSE) Stream
    let es: EventSource | null = null;
    try {
      es = new EventSource('/api/v1/stream');
      es.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.type === 'BUS_EVENT') {
            setEvents((prev) => [payload, ...prev.slice(0, 49)]);
            if (['ORDER_EXECUTED', 'TRADE_DETECTED', 'TRADE_CLOSED'].includes(payload.event_type)) {
              fetchAccount();
              fetchJournal();
              fetchCircuitBreaker();
            }
          } else if (payload.type === 'HEARTBEAT') {
            if (payload.account) setAccount(payload.account);
          }
        } catch (_) {}
      };
    } catch (_) {}

    const interval = setInterval(() => {
      fetchStatus();
      fetchCircuitBreaker();
      fetchJournal();
      fetchPerformance();
      fetchAccount();
      fetchAgents();
      fetchEvents();
    }, 4000);

    return () => {
      clearInterval(interval);
      if (es) es.close();
    };
  }, []);

  const fetchAll = () => {
    fetchStatus();
    fetchStrategies();
    fetchCircuitBreaker();
    fetchAccount();
    fetchJournal();
    fetchPerformance();
    fetchAgents();
    fetchEvents();
  };

  const fetchAgents = async () => {
    try {
      const res = await fetch('/api/v1/agents/');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setAgents(data);
        }
      }
    } catch (_) {}
  };

  const fetchEvents = async () => {
    try {
      const res = await fetch('/api/v1/events/?limit=50');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setEvents(data);
        }
      }
    } catch (_) {}
  };


  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/v1/monitoring/status');
      if (res.ok) {
        const data = await res.json();
        setSystemStatus(data);
        setIsBackendOnline(true);
      } else {
        setIsBackendOnline(false);
      }
    } catch (_) {
      setIsBackendOnline(false);
    }
  };

  const fetchAccount = async () => {
    try {
      const res = await fetch('/api/v1/execution/account');
      if (res.ok) {
        const data = await res.json();
        setAccount(data);
      }
    } catch (_) {}
  };

  const fetchCircuitBreaker = async () => {
    try {
      const res = await fetch('/api/v1/risk/circuit-breaker');
      if (res.ok) {
        const data = await res.json();
        setCircuitBreaker(data);
      }
    } catch (_) {}
  };

  const fetchStrategies = async () => {
    try {
      const res = await fetch('/api/v1/strategies/');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setStrategies(data);
        }
      }
    } catch (_) {}
  };

  const fetchJournal = async () => {
    try {
      const res = await fetch('/api/trades');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setTrades(data);
        }
      } else {
        const fb = await fetch('/api/v1/journal/trades');
        if (fb.ok) {
          const data = await fb.json();
          if (Array.isArray(data)) {
            setTrades(data);
          }
        }
      }
    } catch (_) {}
  };

  const fetchPerformance = async () => {
    try {
      const res = await fetch('/api/performance');
      if (res.ok) {
        const data = await res.json();
        setPerformance(data.metrics || data);
      } else {
        const fb = await fetch('/api/v1/journal/performance');
        if (fb.ok) {
          const data = await fb.json();
          setPerformance(data);
        }
      }
    } catch (_) {}
  };

  // Signal & Order execution handler
  const handleProcessSignal = async (signal: any) => {
    const res = await fetch('/api/v1/execution/process-signal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(signal),
    });
    const data = await res.json();
    fetchCircuitBreaker();
    return data;
  };

  // Backtest runner handler
  const handleRunBacktest = async (req: any) => {
    const res = await fetch('/api/v1/backtest/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    return await res.json();
  };

  // Risk evaluation simulator
  const handleEvaluateRisk = async (req: any) => {
    const res = await fetch('/api/v1/risk/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    return await res.json();
  };

  // Kill switch toggle
  const handleToggleKillSwitch = async (activate: boolean, reason: string) => {
    try {
      const res = await fetch('/api/v1/risk/kill-switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activate, reason, requested_by: 'Dashboard Operator' }),
      });
      if (res.ok) {
        fetchCircuitBreaker();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // ML Training
  const handleTrainRegime = async (symbol: string) => {
    const res = await fetch(`/api/v1/ml/train-regime?symbol=${symbol}&count=500`, {
      method: 'POST',
    });
    return await res.json();
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        killSwitchActive={circuitBreaker.kill_switch_active}
        onEmergencyClick={() => setKillModalOpen(true)}
        systemStatus={systemStatus}
        isBackendOnline={isBackendOnline}
      />

      <main style={{ flex: 1, padding: '1.75rem', maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
        {activeTab === 'overview' && (
          <OverviewPage
            systemStatus={systemStatus}
            account={account}
            circuitBreaker={circuitBreaker}
            agents={agents}
            isBackendOnline={isBackendOnline}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        )}
        {activeTab === 'agents' && (
          <AgentControlCenterPage agents={agents} onRefresh={fetchAgents} />
        )}
        {activeTab === 'live' && (
          <LiveTradingPage onProcessSignal={handleProcessSignal} isBackendOnline={isBackendOnline} />
        )}
        {activeTab === 'strategies' && (
          <StrategiesPage strategies={strategies} />
        )}
        {activeTab === 'backtesting' && (
          <BacktestingPage onRunBacktest={handleRunBacktest} />
        )}
        {activeTab === 'risk' && (
          <RiskPage
            circuitBreaker={circuitBreaker}
            onEmergencyClick={() => setKillModalOpen(true)}
            onEvaluateRisk={handleEvaluateRisk}
          />
        )}
        {activeTab === 'journal' && (
          <JournalPage trades={trades} performance={performance} isBackendOnline={isBackendOnline} />
        )}
        {activeTab === 'research' && (
          <AIResearchPage onTrainRegime={handleTrainRegime} />
        )}
        {activeTab === 'monitoring' && (
          <MonitoringPage
            systemStatus={systemStatus}
            events={events}
            isBackendOnline={isBackendOnline}
            onRefreshEvents={fetchEvents}
          />
        )}
      </main>


      {/* Emergency Kill Switch Modal Dialog */}
      <KillSwitchModal
        isOpen={killModalOpen}
        onClose={() => setKillModalOpen(false)}
        isActive={circuitBreaker.kill_switch_active}
        onToggle={handleToggleKillSwitch}
      />
    </div>
  );
};
