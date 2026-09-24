"""Agent Supervisor: Heartbeat Watchdog, Health Monitor, and Failure Recovery."""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from backend.app.agents.runtime.agent_registry import agent_registry
from backend.app.agents.runtime.agent_types import (
    AgentLifecycleState,
    AgentMetadata,
    AgentPermission,
    AgentRole,
    AgentType,
)
from backend.app.agents.runtime.event_bus import event_bus
from backend.app.core.logging import logger


class AgentSupervisor:
    """Monitors heartbeats, detects stalled agents, and maintains accurate runtime directory."""

    def __init__(self, heartbeat_timeout_seconds: float = 20.0):
        self._heartbeat_timeout = heartbeat_timeout_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def initialize_baseline_agents(self):
        """Register the 11 system agents with verified metadata, tools, and permissions."""
        agents = [
            AgentMetadata(
                agent_id="agent_orchestrator",
                name="Orchestrator Agent",
                description="Coordinates system workflows, manages agent task dependencies, and gates deployment promotions.",
                role=AgentRole.ORCHESTRATOR,
                agent_type=AgentType.AI_REASONING,
                version="1.0.0",
                capabilities=["workflow_coordination", "task_assignment", "gate_validation", "dependency_resolution"],
                permissions=[AgentPermission.COORDINATE_SYSTEM, AgentPermission.READ_MARKET_DATA],
                tools=["TaskDispatcher", "GateEnforcer", "PipelineSynthesizer"],
                model="LLM-Reasoning-Core (Claude-3.5-Sonnet / Gemini-1.5-Pro)",
            ),
            AgentMetadata(
                agent_id="agent_research",
                name="Research Agent",
                description="Generates falsifiable market hypotheses, designs walk-forward test plans, and tracks research experiments.",
                role=AgentRole.RESEARCH,
                agent_type=AgentType.AI_REASONING,
                version="1.0.0",
                capabilities=["hypothesis_generation", "literature_synthesis", "experiment_design", "market_regime_studies"],
                permissions=[AgentPermission.READ_MARKET_DATA, AgentPermission.WRITE_RESEARCH],
                tools=["HistoricalDataExplorer", "HypothesisRegistry", "ExperimentTracker"],
                model="LLM-Hypothesis-Formulator",
            ),
            AgentMetadata(
                agent_id="agent_data",
                name="Data Agent",
                description="Ingests MT5 ticks and candles, performs deterministic integrity audits, and detects gaps or inversions.",
                role=AgentRole.DATA,
                agent_type=AgentType.DETERMINISTIC_SOFTWARE,
                version="1.0.0",
                capabilities=["mt5_ingestion", "high_low_validation", "timestamp_audit", "spread_monitoring"],
                permissions=[AgentPermission.READ_MT5, AgentPermission.WRITE_DATABASE],
                tools=["MT5PriceFeed", "DataQualityAuditor", "BarNormalizer"],
            ),
            AgentMetadata(
                agent_id="agent_strategy",
                name="Strategy Execution Agent",
                description="Evaluates validated deterministic rule sets against price action to emit trade signals.",
                role=AgentRole.STRATEGY,
                agent_type=AgentType.DETERMINISTIC_SOFTWARE,
                version="1.0.0",
                capabilities=["signal_generation", "indicator_computation", "versioned_rule_evaluation"],
                permissions=[AgentPermission.READ_MARKET_DATA, AgentPermission.EVALUATE_SIGNALS],
                tools=["IndicatorEngine", "StrategyRegistry", "SignalEmitter"],
            ),
            AgentMetadata(
                agent_id="agent_ml",
                name="AI / ML Agent",
                description="Extracts leak-free return and volatility features, trains Random Forest market regime classifiers via TimeSeriesSplit CV.",
                role=AgentRole.AI_ML,
                agent_type=AgentType.AI_REASONING,
                version="1.0.0",
                capabilities=["feature_engineering", "regime_classification", "walk_forward_cv", "model_versioning"],
                permissions=[AgentPermission.READ_MARKET_DATA, AgentPermission.TRAIN_MODELS],
                tools=["RandomForestClassifier", "TimeSeriesSplitter", "RegimePredictor"],
                model="Scikit-Learn Ensemble + Probabilistic Classifier",
            ),
            AgentMetadata(
                agent_id="agent_backtest",
                name="Backtest Engine Agent",
                description="Simulates historical execution with realistic spread, slippage, and 95% Monte Carlo drawdown permutations.",
                role=AgentRole.BACKTEST,
                agent_type=AgentType.DETERMINISTIC_SOFTWARE,
                version="1.0.0",
                capabilities=["event_driven_backtest", "slippage_modeling", "spread_cost_simulation", "monte_carlo_analysis"],
                permissions=[AgentPermission.READ_MARKET_DATA, AgentPermission.EXECUTE_BACKTEST],
                tools=["SimulationEngine", "MonteCarloPermutator", "PerformanceAuditor"],
            ),
            AgentMetadata(
                agent_id="agent_risk",
                name="Risk Gate Agent",
                description="Strictly deterministic pre-trade gate enforcing position sizing, max daily loss, max drawdown, and persistent kill switch.",
                role=AgentRole.RISK,
                agent_type=AgentType.DETERMINISTIC_SOFTWARE,
                version="1.0.0",
                capabilities=["pre_trade_sizing", "circuit_breaker_enforcement", "kill_switch_persistence", "exposure_limits"],
                permissions=[AgentPermission.APPROVE_RISK, AgentPermission.READ_MT5],
                tools=["PositionSizer", "DrawdownEnforcer", "CircuitBreakerState", "PersistentKillSwitch"],
            ),
            AgentMetadata(
                agent_id="agent_execution",
                name="Execution Agent",
                description="Deterministic order submission worker, broker response validator, fill reconciler, and idempotency guardian.",
                role=AgentRole.EXECUTION,
                agent_type=AgentType.DETERMINISTIC_SOFTWARE,
                version="1.0.0",
                capabilities=["mt5_order_routing", "idempotency_cache", "fill_reconciliation", "position_synchronization"],
                permissions=[AgentPermission.EXECUTE_ORDERS, AgentPermission.READ_MT5],
                tools=["MT5OrderGateway", "IdempotencyCache", "PositionReconciler"],
            ),
            AgentMetadata(
                agent_id="agent_monitoring",
                name="Monitoring & Watchdog Agent",
                description="Continuously audits MT5 terminal health, database connectivity, latency, spreads, and auto-trips kill switch on disconnect.",
                role=AgentRole.MONITORING,
                agent_type=AgentType.DETERMINISTIC_SOFTWARE,
                version="1.0.0",
                capabilities=["mt5_ipc_watchdog", "database_probe", "spread_watchdog", "auto_kill_switch_trip"],
                permissions=[AgentPermission.MONITOR_HEALTH, AgentPermission.READ_MT5],
                tools=["IPCTerminalProbe", "DatabaseHealthChecker", "SpreadWatchdog", "EmergencyTripHook"],
            ),
            AgentMetadata(
                agent_id="agent_journal",
                name="Journal Agent",
                description="Persists complete immutable trade logs, execution tickets, and R-multiple attribution in the database.",
                role=AgentRole.JOURNAL,
                agent_type=AgentType.DETERMINISTIC_SOFTWARE,
                version="1.0.0",
                capabilities=["immutable_trade_logging", "r_multiple_calculation", "trade_audit_trail"],
                permissions=[AgentPermission.WRITE_JOURNAL, AgentPermission.WRITE_DATABASE],
                tools=["TradeJournalStore", "RAttributionCalculator"],
            ),
            AgentMetadata(
                agent_id="agent_performance",
                name="Performance Analytics Agent",
                description="Computes rigorous statistical metrics (win rate, profit factor, expectancy, drawdown) and synthesizes AI performance reviews.",
                role=AgentRole.PERFORMANCE,
                agent_type=AgentType.AI_REASONING,
                version="1.0.0",
                capabilities=["statistical_attribution", "expectancy_calculation", "regime_performance_breakdown", "ai_insights"],
                permissions=[AgentPermission.COMPUTE_METRICS, AgentPermission.WRITE_RESEARCH],
                tools=["StatisticalAttributor", "DrawdownAnalyzer", "ExpectancyModel"],
                model="Statistical Attribution Engine + LLM Insight Synthesizer",
            ),
        ]

        for meta in agents:
            agent_registry.register_agent(meta)

    async def start(self):
        """Start the supervisor background watchdog loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._supervision_loop())
        logger.info("Agent Supervisor background loop started.")

    async def stop(self):
        """Stop supervisor loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Agent Supervisor background loop stopped.")

    async def _supervision_loop(self):
        """Periodic heartbeat and liveness monitoring loop."""
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                agents = agent_registry.get_all_agents()

                for item in agents:
                    aid = item["metadata"]["agent_id"]
                    st = item["state"]
                    hb = st.get("heartbeat_timestamp")
                    curr_status = st.get("status")

                    if hb:
                        if isinstance(hb, str):
                            from datetime import datetime as dt
                            try:
                                hb_dt = dt.fromisoformat(hb)
                            except Exception:
                                hb_dt = now
                        else:
                            hb_dt = hb

                        elapsed = (now - hb_dt).total_seconds()

                        # If agent is silent longer than timeout, update state
                        if elapsed > self._heartbeat_timeout and curr_status not in [
                            AgentLifecycleState.OFFLINE.value,
                            AgentLifecycleState.ERROR.value,
                            AgentLifecycleState.STOPPED.value,
                        ]:
                            agent_registry.update_status(
                                aid,
                                AgentLifecycleState.WAITING,
                                error_message=f"No heartbeat received in {elapsed:.1f}s",
                            )

                await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Agent Supervisor loop: {e}")
                await asyncio.sleep(2.0)


# Global singleton instance
agent_supervisor = AgentSupervisor()
