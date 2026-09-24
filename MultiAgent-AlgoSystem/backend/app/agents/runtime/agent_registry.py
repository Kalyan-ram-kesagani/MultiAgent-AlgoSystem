"""Agent Registry: Central Directory, Task Dispatcher, and Lifecycle Manager."""
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import uuid

from backend.app.agents.runtime.agent_types import (
    AgentLifecycleState,
    AgentMetadata,
    AgentPermission,
    AgentRole,
    AgentState,
    AgentTask,
    AgentType,
    TaskStatus,
)
from backend.app.agents.runtime.event_bus import event_bus
from backend.app.core.logging import logger


class AgentRegistry:
    """Central registry and lifecycle coordinator for all system agents."""

    def __init__(self):
        self._metadata: Dict[str, AgentMetadata] = {}
        self._states: Dict[str, AgentState] = {}
        self._tasks: Dict[str, AgentTask] = {}
        self._task_history_by_agent: Dict[str, List[str]] = {}
        self._db_session_factory = None

    def set_session_factory(self, factory):
        """Connect database session factory for persisting agent states and tasks."""
        self._db_session_factory = factory

    def _sync_agent_to_db(self, agent_id: str):
        """Asynchronously sync agent state to Supabase PostgreSQL."""
        if not self._db_session_factory:
            return
        st = self._states.get(agent_id)
        meta = self._metadata.get(agent_id)
        if not st:
            return

        import asyncio
        async def _do_sync():
            try:
                from sqlalchemy import select
                from backend.app.models.agent_state import AgentStateModel
                async with self._db_session_factory() as session:
                    stmt = select(AgentStateModel).where(AgentStateModel.agent_id == agent_id)
                    res = await session.execute(stmt)
                    record = res.scalar_one_or_none()
                    if not record:
                        record = AgentStateModel(
                            agent_id=agent_id,
                            status=st.status.value if hasattr(st.status, "value") else str(st.status),
                            version=meta.version if meta else "1.0.0",
                            started_at=st.heartbeat_timestamp,
                            last_heartbeat=st.heartbeat_timestamp,
                            current_task=st.current_task,
                            tasks_completed=st.tasks_completed_today,
                            tasks_failed=0,
                            last_error=st.error_message,
                            extra_metadata=st.metrics,
                        )
                        session.add(record)
                    else:
                        record.status = st.status.value if hasattr(st.status, "value") else str(st.status)
                        record.last_heartbeat = st.heartbeat_timestamp
                        record.current_task = st.current_task
                        record.tasks_completed = st.tasks_completed_today
                        record.last_error = st.error_message
                        record.extra_metadata = st.metrics
                    await session.commit()
            except Exception as e:
                logger.debug(f"Agent DB sync note: {e}")

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_do_sync())
        except RuntimeError:
            pass

    def _sync_task_to_db(self, task: AgentTask):
        """Asynchronously persist task to Supabase PostgreSQL."""
        if not self._db_session_factory:
            return

        import asyncio
        async def _do_task_sync():
            try:
                from sqlalchemy import select
                from backend.app.models.agent_state import AgentTaskModel
                async with self._db_session_factory() as session:
                    stmt = select(AgentTaskModel).where(AgentTaskModel.task_id == task.task_id)
                    res = await session.execute(stmt)
                    record = res.scalar_one_or_none()
                    if not record:
                        record = AgentTaskModel(
                            task_id=task.task_id,
                            agent_id=task.agent_id,
                            task_type=task.name,
                            status=task.status.value if hasattr(task.status, "value") else str(task.status),
                            priority=5,
                            payload=task.input_payload,
                            result=task.output_payload,
                            error=task.error_message,
                            created_at=task.created_at,
                            started_at=task.started_at,
                            completed_at=task.completed_at,
                        )
                        session.add(record)
                    else:
                        record.status = task.status.value if hasattr(task.status, "value") else str(task.status)
                        record.result = task.output_payload
                        record.error = task.error_message
                        record.completed_at = task.completed_at
                    await session.commit()
            except Exception as e:
                logger.debug(f"Task DB sync note: {e}")

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_do_task_sync())
        except RuntimeError:
            pass

    def register_agent(self, metadata: AgentMetadata) -> AgentState:
        """Register an agent into the runtime directory."""
        self._metadata[metadata.agent_id] = metadata
        state = AgentState(
            agent_id=metadata.agent_id,
            name=metadata.name,
            status=AgentLifecycleState.IDLE,
            heartbeat_timestamp=datetime.now(timezone.utc),
            tasks_completed_today=0,
            metrics={"uptime_seconds": 0, "success_rate": 100.0},
        )
        self._states[metadata.agent_id] = state
        self._task_history_by_agent[metadata.agent_id] = []
        self._sync_agent_to_db(metadata.agent_id)

        logger.info(
            f"Agent registered: {metadata.name} [{metadata.agent_id}] ({metadata.role.value})",
            extra={"agent_id": metadata.agent_id, "role": metadata.role.value},
        )
        return state

    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Retrieve agent metadata."""
        return self._metadata.get(agent_id)

    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Retrieve agent runtime state."""
        return self._states.get(agent_id)

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Return combined metadata and state for all registered agents."""
        results = []
        for aid, meta in self._metadata.items():
            st = self._states.get(aid)
            item = {
                "metadata": meta.model_dump(),
                "state": st.model_dump() if st else {},
            }
            results.append(item)
        return results

    def heartbeat(self, agent_id: str) -> bool:
        """Record a heartbeat timestamp for an agent."""
        if agent_id in self._states:
            self._states[agent_id].heartbeat_timestamp = datetime.now(timezone.utc)
            if self._states[agent_id].status == AgentLifecycleState.OFFLINE:
                self._states[agent_id].status = AgentLifecycleState.IDLE
            return True
        return False

    def update_status(
        self,
        agent_id: str,
        status: AgentLifecycleState,
        current_task: Optional[str] = None,
        error_message: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ):
        """Update mutable status of an agent."""
        if agent_id in self._states:
            st = self._states[agent_id]
            prev_status = st.status
            st.status = status
            st.heartbeat_timestamp = datetime.now(timezone.utc)
            if current_task is not None:
                st.current_task = current_task
            if error_message is not None:
                st.error_message = error_message
            if metrics:
                st.metrics.update(metrics)

            if status == AgentLifecycleState.ERROR:
                event_bus._history.append(
                    event_bus.publish(
                        event_type="AGENT_ERROR",
                        component=agent_id,
                        level="CRITICAL",
                        message=f"Agent {st.name} entered ERROR state: {error_message}",
                        details={"status": status.value, "prev_status": prev_status.value},
                    )
                )
            self._sync_agent_to_db(agent_id)

    def assign_task(
        self,
        agent_id: str,
        name: str,
        input_payload: Dict[str, Any],
    ) -> AgentTask:
        """Create and assign a task to an agent."""
        task_id = f"TSK-{uuid.uuid4().hex[:8].upper()}"
        task = AgentTask(
            task_id=task_id,
            agent_id=agent_id,
            name=name,
            created_at=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc),
            status=TaskStatus.RUNNING,
            input_payload=input_payload,
        )
        self._tasks[task_id] = task
        if agent_id not in self._task_history_by_agent:
            self._task_history_by_agent[agent_id] = []
        self._task_history_by_agent[agent_id].append(task_id)

        if agent_id in self._states:
            st = self._states[agent_id]
            st.status = AgentLifecycleState.WORKING
            st.current_task = name
            st.current_task_id = task_id
            st.heartbeat_timestamp = datetime.now(timezone.utc)

        self._sync_agent_to_db(agent_id)
        self._sync_task_to_db(task)
        return task

    def report_result(
        self,
        agent_id: str,
        task_id: str,
        status: TaskStatus,
        output_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> Optional[AgentTask]:
        """Report completion or failure of an assigned task."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        now = datetime.now(timezone.utc)
        task.completed_at = now
        task.status = status
        task.output_payload = output_payload
        task.error_message = error_message
        if task.started_at:
            task.duration_ms = (now - task.started_at).total_seconds() * 1000

        if agent_id in self._states:
            st = self._states[agent_id]
            st.last_task = task.name
            st.last_result = "SUCCESS" if status == TaskStatus.COMPLETED else f"FAILED: {error_message}"
            st.last_action_timestamp = now
            st.current_task = None
            st.current_task_id = None
            st.status = AgentLifecycleState.IDLE if status == TaskStatus.COMPLETED else AgentLifecycleState.ERROR
            if status == TaskStatus.COMPLETED:
                st.tasks_completed_today += 1
            st.heartbeat_timestamp = now

        self._sync_agent_to_db(agent_id)
        self._sync_task_to_db(task)
        return task

    def get_tasks(self, agent_id: Optional[str] = None, limit: int = 50) -> List[AgentTask]:
        """Retrieve recent tasks."""
        if agent_id:
            task_ids = self._task_history_by_agent.get(agent_id, [])
            tasks = [self._tasks[tid] for tid in task_ids if tid in self._tasks]
        else:
            tasks = list(self._tasks.values())
        return list(reversed(tasks[-limit:]))


# Global singleton instance
agent_registry = AgentRegistry()
