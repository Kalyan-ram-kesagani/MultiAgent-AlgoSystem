"""Agent Registry, Runtime Telemetry, and Task API endpoints."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.agents.runtime import (
    agent_registry,
    event_bus,
    AgentLifecycleState,
    AgentMetadata,
    AgentState,
    AgentTask,
    TaskStatus,
)

router = APIRouter(prefix="/agents", tags=["Agent Runtime"])


class TaskAssignmentRequest(BaseModel):
    name: str
    payload: Dict[str, Any] = {}


@router.get("/")
def list_all_agents():
    """Retrieve all 11 system agents with live runtime status, heartbeats, and metrics."""
    return agent_registry.get_all_agents()


@router.get("/{agent_id}")
def get_agent_detail(agent_id: str):
    """Retrieve full details, capabilities, permissions, and tools for a specific agent."""
    meta = agent_registry.get_agent(agent_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    state = agent_registry.get_agent_state(agent_id)
    tasks = agent_registry.get_tasks(agent_id=agent_id, limit=10)
    return {
        "metadata": meta.model_dump(),
        "state": state.model_dump() if state else {},
        "recent_tasks": [t.model_dump() for t in tasks],
    }


@router.post("/{agent_id}/heartbeat")
def heartbeat_agent(agent_id: str):
    """Update heartbeat timestamp for an agent."""
    ok = agent_registry.heartbeat(agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    return {"status": "HEARTBEAT_ACKNOWLEDGED", "agent_id": agent_id}


@router.post("/{agent_id}/task", response_model=AgentTask)
def assign_agent_task(agent_id: str, req: TaskAssignmentRequest):
    """Assign an on-demand task to a registered agent."""
    meta = agent_registry.get_agent(agent_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    task = agent_registry.assign_task(agent_id=agent_id, name=req.name, input_payload=req.payload)
    return task


@router.get("/{agent_id}/tasks", response_model=List[AgentTask])
def get_agent_tasks(agent_id: str, limit: int = Query(default=20, ge=1, le=100)):
    """Retrieve chronological task history for an agent."""
    return agent_registry.get_tasks(agent_id=agent_id, limit=limit)


@router.get("/{agent_id}/events")
def get_agent_events(agent_id: str, limit: int = Query(default=50, ge=1, le=200)):
    """Retrieve recent structured events associated with a specific agent."""
    all_events = event_bus.get_recent_events(limit=200)
    agent_evs = [
        e.model_dump()
        for e in all_events
        if e.component == agent_id
        or (e.details and e.details.get("agent_id") == agent_id)
        or agent_id in e.message
    ]
    return agent_evs[:limit]


# Event Stream Router mounted alongside
events_router = APIRouter(prefix="/events", tags=["System Events"])


@events_router.get("/")
def get_system_events(

    limit: int = Query(default=50, ge=1, le=200),
    level: Optional[str] = Query(default=None),
):
    """Retrieve recent structured auditable events emitted across all agents."""
    events = event_bus.get_recent_events(limit=limit, level=level)
    return [e.model_dump() for e in events]
