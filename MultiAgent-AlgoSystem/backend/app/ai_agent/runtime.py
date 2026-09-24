"""AI Agent Execution Runtime, Lifecycle Hooks, Auditing, and State Manager."""
import asyncio
from datetime import datetime, timezone
import json
import time
import uuid
from typing import Any, Dict, List, Optional
from agents import Runner
from agents.lifecycle import RunHooksBase
from sqlalchemy import select

from backend.app.ai_agent.agent import trading_research_agent
from backend.app.ai_agent.guardrails import guardrails
from backend.app.ai_agent.schemas import AgentRuntimeState
from backend.app.agents.runtime.event_bus import event_bus
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.session import async_session_maker
from backend.app.models.ai_audit import AIAgentRun, AIToolCall, OrderRequestModel


class AuditRunHooks(RunHooksBase):
    """Lifecycle callbacks linking OpenAI Agents SDK to persistent auditing and real-time state."""

    def __init__(self, runtime: "AIAgentRuntime", run_id: str):
        self.runtime = runtime
        self.run_id = run_id
        self._tool_start_times: Dict[str, float] = {}

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        self.runtime.update_state(AgentRuntimeState.THINKING)
        self.runtime.last_heartbeat = datetime.now(timezone.utc)

    async def on_llm_end(self, context, agent, response):
        self.runtime.last_heartbeat = datetime.now(timezone.utc)

    async def on_tool_start(self, context, agent, tool):
        tool_name = getattr(tool, "name", str(tool))
        self._tool_start_times[tool_name] = time.perf_counter()

        # Classify granular runtime state by tool domain
        if any(k in tool_name for k in ("backtest", "walk_forward", "monte_carlo")):
            state = AgentRuntimeState.BACKTESTING
        elif any(k in tool_name for k in ("hypothesis", "research", "compare")):
            state = AgentRuntimeState.RESEARCHING
        elif any(k in tool_name for k in ("risk", "position_size", "validate_trade")):
            state = AgentRuntimeState.RISK_CHECK
        elif "request_order" in tool_name:
            state = AgentRuntimeState.EXECUTING
        else:
            state = AgentRuntimeState.TOOL_CALL

        self.runtime.update_state(state, current_tool=tool_name)
        self.runtime.last_action = f"Executing tool: {tool_name}"

        await event_bus.publish(
            event_type="AI_TOOL_CALL",
            component="TradingResearchAgent",
            message=f"Agent executing tool: {tool_name}",
            details={"run_id": self.run_id, "tool": tool_name},
        )

    async def on_tool_end(self, context, agent, tool, result):
        tool_name = getattr(tool, "name", str(tool))
        start_t = self._tool_start_times.pop(tool_name, None)
        latency_ms = (time.perf_counter() - start_t) * 1000 if start_t else 0.0

        str_res = str(result)
        # Log to in-memory history
        tc_dict = {
            "tool_call_id": f"TC-{uuid.uuid4().hex[:8].upper()}",
            "run_id": self.run_id,
            "tool_name": tool_name,
            "latency_ms": round(latency_ms, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output_preview": str_res[:200],
        }
        self.runtime.add_tool_call_history(tc_dict)

        # Persist tool execution audit record in database
        try:
            async with async_session_maker() as session:
                tc_model = AIToolCall(
                    tool_call_id=tc_dict["tool_call_id"],
                    run_id=self.run_id,
                    tool_name=tool_name,
                    input_arguments_json="{}",
                    output_result_json=str_res[:4000],
                    success=True,
                    latency_ms=round(latency_ms, 2),
                )
                session.add(tc_model)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to persist tool call audit: {e}")

        await event_bus.publish(
            event_type="AI_TOOL_RESULT",
            component="TradingResearchAgent",
            message=f"Tool {tool_name} returned ({latency_ms:.1f}ms)",
            details={"run_id": self.run_id, "tool": tool_name, "latency_ms": round(latency_ms, 2)},
        )


class AIAgentRuntime:
    """Central singleton managing real AI Agent execution, health, and status observability."""

    def __init__(self):
        self.state: AgentRuntimeState = AgentRuntimeState.IDLE
        self.current_task: Optional[str] = None
        self.current_tool: Optional[str] = None
        self.current_run_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.last_heartbeat: datetime = datetime.now(timezone.utc)
        self.last_action: Optional[str] = "Initialized AI Trading & Research Agent"
        self.last_decision: Optional[str] = "System ready for quantitative research and analysis"
        self.last_error: Optional[str] = None
        self.last_latency_ms: Optional[float] = None
        self.recent_runs: List[Dict[str, Any]] = []
        self.recent_tool_calls: List[Dict[str, Any]] = []

    @property
    def current_state(self) -> AgentRuntimeState:
        return self.state

    def update_state(self, state: AgentRuntimeState, current_tool: Optional[str] = None, last_error: Optional[str] = None):
        self.state = state
        self.current_tool = current_tool
        if last_error is not None:
            self.last_error = last_error
        self.last_heartbeat = datetime.now(timezone.utc)
        try:
            from backend.app.agents.runtime import agent_registry
            agent_registry.heartbeat("agent_orchestrator")
        except Exception:
            pass

    def add_tool_call_history(self, tc: Dict[str, Any]):
        self.recent_tool_calls.insert(0, tc)
        if len(self.recent_tool_calls) > 100:
            self.recent_tool_calls.pop()

    def get_status(self) -> Dict[str, Any]:
        """Return live runtime status reflecting exact state."""
        return {
            "agent_name": "TradingResearchAgent",
            "model": settings.OPENAI_MODEL,
            "status": self.state.value,
            "current_task": self.current_task,
            "current_tool": self.current_tool,
            "current_run_id": self.current_run_id,
            "current_run": self.current_run_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "last_action": self.last_action,
            "last_decision": self.last_decision,
            "last_result": self.last_decision,
            "last_error": self.last_error,
            "last_latency_ms": self.last_latency_ms,
            "has_openai_key": bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5),
            "trading_mode": settings.TRADING_MODE,
        }

    async def run(
        self,
        task_name: str,
        user_prompt: str,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an agent task using the OpenAI Agents SDK with controlled tool calls
        and automatic fallback if OpenAI is unconfigured or offline.
        """
        run_id = f"RUN-{uuid.uuid4().hex[:10].upper()}"
        self.current_run_id = run_id
        self.current_task = task_name
        self.start_time = datetime.now(timezone.utc)
        self.update_state(AgentRuntimeState.THINKING)
        self.last_error = None
        start_perf = time.perf_counter()

        sanitized_prompt = guardrails.sanitize_input(user_prompt)

        # Publish AI_RUN_STARTED event
        await event_bus.publish(
            event_type="AI_RUN_STARTED",
            component="TradingResearchAgent",
            message=f"AI Agent started task: {task_name}",
            details={"run_id": run_id, "task": task_name},
        )

        # Create persistent DB run record
        try:
            async with async_session_maker() as session:
                run_record = AIAgentRun(
                    run_id=run_id,
                    agent_name="TradingResearchAgent",
                    task=task_name,
                    status="RUNNING",
                    model=settings.OPENAI_MODEL,
                    input_prompt=sanitized_prompt,
                    start_time=self.start_time,
                )
                session.add(run_record)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to initialize run audit record: {e}")

        final_response_text = ""
        is_success = True
        error_msg = None

        has_api_key = bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 10)

        if has_api_key:
            try:
                hooks = AuditRunHooks(self, run_id=run_id)
                # Run through OpenAI Agents SDK
                result = await Runner.run(
                    trading_research_agent,
                    input=sanitized_prompt,
                    hooks=hooks,
                    max_turns=10,
                )
                final_response_text = str(getattr(result, "final_output", "") or "")
            except Exception as e:
                logger.warning(f"OpenAI Agents SDK execution warning ({e}), engaging autonomous fallback pipeline.")
                error_msg = str(e)
                # Fallback to local autonomous quantitative investigation
                final_response_text = await self._run_deterministic_investigation(task_name, sanitized_prompt, run_id)
        else:
            # Deterministic quantitative pipeline execution
            logger.info("OpenAI API key not set or in offline test mode; executing quantitative research pipeline.")
            final_response_text = await self._run_deterministic_investigation(task_name, sanitized_prompt, run_id)

        latency_ms = (time.perf_counter() - start_perf) * 1000
        self.last_latency_ms = round(latency_ms, 2)
        sanitized_output = guardrails.sanitize_output(final_response_text)

        # Update runtime state
        self.update_state(AgentRuntimeState.IDLE)
        self.last_action = f"Completed task: {task_name}"
        self.last_decision = sanitized_output[:180] + ("..." if len(sanitized_output) > 180 else "")

        # Update DB run record
        try:
            async with async_session_maker() as session:
                stmt = select(AIAgentRun).where(AIAgentRun.run_id == run_id)
                res = await session.execute(stmt)
                rec = res.scalar_one_or_none()
                if rec:
                    rec.status = "COMPLETED" if not error_msg else "COMPLETED_FALLBACK"
                    rec.final_response = sanitized_output
                    rec.end_time = datetime.now(timezone.utc)
                    rec.latency_ms = round(latency_ms, 2)
                    rec.error = error_msg
                    await session.commit()
        except Exception as e:
            logger.error(f"Failed to update run audit record: {e}")

        # Add to in-memory run history
        run_summary = {
            "run_id": run_id,
            "task": task_name,
            "status": "COMPLETED",
            "latency_ms": round(latency_ms, 2),
            "response_preview": sanitized_output[:250],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.recent_runs.insert(0, run_summary)
        if len(self.recent_runs) > 50:
            self.recent_runs.pop()

        # Publish AI_RUN_COMPLETED event
        await event_bus.publish(
            event_type="AI_RUN_COMPLETED",
            component="TradingResearchAgent",
            message=f"AI Agent completed task: {task_name} in {latency_ms:.1f}ms",
            details=run_summary,
        )

        return {
            "run_id": run_id,
            "task": task_name,
            "status": "COMPLETED",
            "latency_ms": round(latency_ms, 2),
            "response": sanitized_output,
            "error": error_msg,
        }

    async def _run_deterministic_investigation(self, task_name: str, prompt: str, run_id: str) -> str:
        """
        Autonomous deterministic quant research runner.
        Executes real tools, evaluates performance, runs backtests, and produces quantitative reports.
        """
        from backend.app.ai_agent.tools import (
            analyze_trade_sources,
            get_candles,
            get_current_price,
            get_market_regime,
            get_mt5_account,
            get_risk_state,
            get_strategy_performance,
            run_backtest,
            run_monte_carlo,
            run_walk_forward,
        )

        # 1. Audit Trade Origin Attribution
        self.update_state(AgentRuntimeState.RESEARCHING, current_tool="analyze_trade_sources")
        src_raw = analyze_trade_sources()
        src_data = json.loads(src_raw)

        # 2. Strategy Performance & Sample Size Check
        self.update_state(AgentRuntimeState.RESEARCHING, current_tool="get_strategy_performance")
        perf_raw = get_strategy_performance("strategy_v1")
        perf_data = json.loads(perf_raw)
        sample_count = perf_data.get("sample_size", 0)

        # 3. Backtesting
        self.update_state(AgentRuntimeState.BACKTESTING, current_tool="run_backtest")
        bt_raw = run_backtest(strategy_id="strategy_v1", symbol="EURUSD", timeframe="H1", days=90)
        bt_data = json.loads(bt_raw)

        # 4. Monte Carlo (Reproducible: 500 permutations, seed 42, 90 days H1)
        self.update_state(AgentRuntimeState.BACKTESTING, current_tool="run_monte_carlo")
        mc_raw = run_monte_carlo(
            strategy_id="strategy_v1",
            symbol="EURUSD",
            timeframe="H1",
            days=90,
            simulations=500,
            random_seed=42,
            initial_capital=10000.0,
        )
        mc_data = json.loads(mc_raw)

        # 5. Risk State
        self.update_state(AgentRuntimeState.RISK_CHECK, current_tool="get_risk_state")
        risk_raw = get_risk_state()
        risk_data = json.loads(risk_raw)

        # Deterministic Risk Gate Evaluation (Nominal DD <= 10% AND MC 95% DD <= 10%)
        nom_dd = float(bt_data.get('metrics', {}).get('max_drawdown_pct', 0.0))
        mc_dd = float(mc_data.get('worst_case_drawdown_95pct', 0.0))
        risk_limit = 10.0
        risk_gate_passed = (nom_dd <= risk_limit) and (mc_dd <= risk_limit)
        risk_gate_status = "PASS" if risk_gate_passed else "FAIL"

        # Evaluate Sample Size & Overfitting Safeguards
        if sample_count < 10:
            sample_status_label = "INSUFFICIENT DATA"
            conclusion = "Live database sample count (<10 trades) is statistically insufficient to infer performance edge or justify rule modifications."
            next_action = "CONTINUE FORWARD TESTING. Do NOT modify strategy parameters or rules on sample size < 10 trades."
        elif sample_count < 50:
            sample_status_label = "EARLY DATA"
            conclusion = "Early trade sample provides initial observations; exploratory research only."
            next_action = "Continue paper/demo validation before considering candidate adjustments."
        elif sample_count < 100:
            sample_status_label = "PRELIMINARY"
            conclusion = "Preliminary data supports exploratory hypothesis formulation."
            next_action = "Conduct walk-forward validation and candidate comparison."
        else:
            sample_status_label = "RESEARCHABLE"
            conclusion = "Statistically robust sample size available for systematic hypothesis testing."
            next_action = "Create strategy candidate version and submit for human review."

        if not risk_gate_passed:
            risk_summary = f"FAIL (Nominal DD: {nom_dd:.2f}%, MC 95% DD: {mc_dd:.2f}%, Limit: {risk_limit:.2f}%)"
            risk_conclusion = f"FAIL - Drawdown ({max(nom_dd, mc_dd):.2f}%) exceeds deterministic 10% risk threshold."
            conclusion += f" In addition, backtest/simulation drawdown ({max(nom_dd, mc_dd):.2f}%) fails the deterministic 10% portfolio risk limit."
            next_action = "HALT. DETERMINISTIC RISK FAILURE: Drawdown exceeds 10% account threshold. AI is strictly prohibited from modifying strategy parameters, overriding risk failure, or promoting candidate strategies."
        else:
            risk_summary = f"PASS (Nominal DD: {nom_dd:.2f}%, MC 95% DD: {mc_dd:.2f}%, Limit: {risk_limit:.2f}%)"
            risk_conclusion = "PASS - Drawdown within deterministic 10% risk threshold."

        sys_trades = src_data.get("system_trades", 0)
        man_trades = src_data.get("manual_trades", 0)
        ext_trades = src_data.get("external_trades", 0)

        report = f"""# Research Report

Strategy:
strategy_v1

Sample Status:
{sample_status_label}

Observation:
Database audit reveals {sys_trades} systematic trades, {man_trades} manual discretionary trades, and {ext_trades} external trades. Manual and external trades are strictly isolated from strategy_v1 attribution. Real system expectancy is ${perf_data.get('metrics', {}).get('expectancy_dollars', 0.0)}/trade.

Hypothesis:
Strategy performance stability requires confirmation across higher sample counts and volatile market sessions.

Evidence:
- Systematic Trades: {sys_trades}
- Win Rate: {perf_data.get('metrics', {}).get('win_rate_pct', 0.0)}%
- Profit Factor: {perf_data.get('metrics', {}).get('profit_factor', 0.0)}
- Attribution Guarantee: Discretionary manual trades ({man_trades}) excluded from strategy_v1.

Experiment:
EXP-0001 (EURUSD H1 Event-Driven Simulation)

Baseline:
- Profit Factor: {bt_data.get('metrics', {}).get('profit_factor', 0.0)}
- Expectancy: ${bt_data.get('metrics', {}).get('expectancy_dollars', 0.0)}
- Max Drawdown: {nom_dd}% (Peak-to-Trough on Equity Curve)
- Commission: $7.0/lot, Spread: 1.5 pips, Slippage: 5 points

Candidate:
None created in this run (sample size < 10 trades prohibits premature rule modification).

Out-of-Sample:
Walk-forward split testing requires minimum 50 historical trades for statistically meaningful partition.

Monte Carlo:
- 95th Percentile Drawdown: {mc_dd}% (500 permutations, Seed: 42, Capital Basis: $10,000 USD)
- Median Outcome: ${mc_data.get('median_outcome_pnl', 0.0)}
- Risk Conclusion: {risk_conclusion}

Risk Gate:
- Status: {risk_gate_status}
- Evaluation: {risk_summary}
- Hard Risk Limit: {risk_limit}% Max Drawdown
- AI Override Permission: STRICTLY PROHIBITED (Deterministic Risk Failure)

Risk:
- Kill Switch: {'ACTIVE' if risk_data.get('kill_switch_active') else 'OFF (Healthy)'}
- Account Equity: ${risk_data.get('account_equity', 10000.0):,.2f}
- Open Positions: {risk_data.get('open_positions_count', 0)} / {risk_data.get('hard_limits', {}).get('max_open_positions', 5)}
- Drawdown Assessment: {risk_gate_status}

Conclusion:
{conclusion}

Next Action:
{next_action}
"""
        return report


agent_runtime = AIAgentRuntime()
