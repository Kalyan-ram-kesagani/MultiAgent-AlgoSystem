"""Asynchronous Event Bus with Pub/Sub and Database Persistence."""
import asyncio
from datetime import datetime, timezone
import json
from typing import Any, Callable, Coroutine, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.logging import logger


class Event(BaseModel):
    """Structured audit event."""
    event_id: str
    event_type: str
    component: str
    level: str = "INFO"  # INFO, WARNING, CRITICAL
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = Field(default_factory=dict)


class EventBus:
    """Central asynchronous Event Bus coordinating inter-agent events and logging."""

    def __init__(self, max_history: int = 200):
        self._subscribers: Dict[str, List[Callable[[Event], Coroutine[Any, Any, None]]]] = {}
        self._history: List[Event] = []
        self._max_history = max_history
        self._db_session_factory = None

    def set_session_factory(self, factory):
        """Optionally connect a database session factory for event persistence."""
        self._db_session_factory = factory

    def subscribe(self, event_type: str, handler: Callable[[Event], Coroutine[Any, Any, None]]):
        """Register an async handler for a specific event type or wildcard '*'."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Coroutine[Any, Any, None]]):
        """Unregister an async handler for a specific event type."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    async def publish(
        self,
        event_type: str,
        component: str,
        message: str,
        level: str = "INFO",
        details: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """Publish an event to all subscribers and persist to storage."""
        import uuid
        event = Event(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            event_type=event_type,
            component=component,
            level=level,
            message=message,
            timestamp=datetime.now(timezone.utc),
            details=details or {},
        )

        # Append to ring buffer
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # Log event structured
        log_level = logger.info
        if level == "WARNING":
            log_level = logger.warning
        elif level == "CRITICAL":
            log_level = logger.error
        log_level(f"[{component}] {event_type}: {message}", extra={"event": event.model_dump(mode="json")})


        # Persist to database if session factory is available
        if self._db_session_factory:
            asyncio.create_task(self._persist_to_db(event))

        # Notify specific subscribers
        handlers = list(self._subscribers.get(event_type, []))
        # Notify wildcard subscribers
        handlers.extend(self._subscribers.get("*", []))

        for handler in handlers:
            try:
                res = handler(event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error(f"Error executing event subscriber for {event_type}: {e}")


        return event

    async def _persist_to_db(self, event: Event):
        """Asynchronously insert event into system_events and agent_events tables."""
        try:
            from backend.app.models.system import SystemEvent
            from backend.app.models.agent_state import AgentEventModel
            async with self._db_session_factory() as session:
                record = SystemEvent(
                    timestamp=event.timestamp,
                    level=event.level,
                    component=event.component,
                    event_type=event.event_type,
                    message=event.message,
                    details_json=json.dumps(event.details),
                )
                session.add(record)

                agent_id = event.details.get("agent_id") or (event.component if "agent" in event.component.lower() else None)
                task_id = event.details.get("task_id")
                agent_event = AgentEventModel(
                    timestamp=event.timestamp,
                    agent_id=agent_id,
                    event_type=event.event_type,
                    task_id=task_id,
                    message=event.message,
                    event_metadata=event.details,
                )
                session.add(agent_event)

                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to persist event to DB: {e}")

    def get_recent_events(self, limit: int = 50, level: Optional[str] = None) -> List[Event]:
        """Return chronological recent events."""
        events = self._history
        if level:
            events = [e for e in events if e.level == level]
        return list(reversed(events[-limit:]))


# Global singleton instance
event_bus = EventBus()
