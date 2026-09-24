"""Unit tests for Agent Runtime, Agent Registry, Event Bus, and Supervisor."""
import pytest
from backend.app.agents.runtime import (
    AgentLifecycleState,
    AgentMetadata,
    AgentPermission,
    AgentRegistry,
    AgentRole,
    AgentSupervisor,
    AgentType,
    EventBus,
    TaskStatus,
)


def test_agent_registry_lifecycle():
    registry = AgentRegistry()
    meta = AgentMetadata(
        agent_id="test_worker",
        name="Test Worker",
        description="Worker for unit testing",
        role=AgentRole.DATA,
        agent_type=AgentType.DETERMINISTIC_SOFTWARE,
        capabilities=["test_action"],
        permissions=[AgentPermission.READ_MARKET_DATA],
    )
    state = registry.register_agent(meta)
    assert state.agent_id == "test_worker"
    assert state.status == AgentLifecycleState.IDLE

    # Assign task
    task = registry.assign_task("test_worker", "process_bars", {"count": 100})
    assert task.status == TaskStatus.RUNNING
    assert registry.get_agent_state("test_worker").status == AgentLifecycleState.WORKING

    # Report completion
    finished = registry.report_result("test_worker", task.task_id, TaskStatus.COMPLETED, {"result": "OK"})
    assert finished.status == TaskStatus.COMPLETED
    assert finished.duration_ms is not None
    assert registry.get_agent_state("test_worker").status == AgentLifecycleState.IDLE
    assert registry.get_agent_state("test_worker").tasks_completed_today == 1


@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    bus = EventBus()
    received = []

    async def sample_handler(evt):
        received.append(evt)

    bus.subscribe("ORDER_FILLED", sample_handler)
    evt = await bus.publish(
        event_type="ORDER_FILLED",
        component="test_execution",
        message="Order #123 filled",
        details={"ticket": 123},
    )

    assert evt.event_type == "ORDER_FILLED"
    assert len(received) == 1
    assert received[0].details["ticket"] == 123


def test_agent_supervisor_baseline_initialization():
    supervisor = AgentSupervisor()
    supervisor.initialize_baseline_agents()
    from backend.app.agents.runtime import agent_registry
    all_agents = agent_registry.get_all_agents()
    assert len(all_agents) == 11
    agent_ids = [a["metadata"]["agent_id"] for a in all_agents]
    assert "agent_orchestrator" in agent_ids
    assert "agent_risk" in agent_ids
    assert "agent_execution" in agent_ids
