"""
Browser Session Manager
========================

Manages active browser sessions across the application.
Provides session tracking, cleanup, and lifecycle management.

Design Decisions:
- Singleton pattern — one manager per application instance.
- Tracks all active sessions (driver + contexts) for graceful shutdown.
- Integrates with FastAPI lifespan events for startup/shutdown.
- Session IDs are UUIDs for uniqueness across concurrent executions.
- Not a browser pool (that's Phase 7). This is a registry of active sessions.

Usage:
    manager = BrowserSessionManager.get_instance()
    session_id = await manager.create_session(engine, config)
    ctx = await manager.get_context(session_id)
    await manager.close_session(session_id)
    
    # On app shutdown:
    await manager.shutdown_all()
"""

from __future__ import annotations

import asyncio
import uuid
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

from backend.automation.base_driver import BaseDriver, BaseExecutionContext
from backend.automation.config import BrowserConfig, RuntimeEngine, FeatureFlags
from backend.automation.observability import (
    get_automation_logger,
    ExecutionTracer,
    MetricsCollector,
)

logger = get_automation_logger(
    "automation.session_manager",
    engine="manager",
    phase=2,
    component="session",
)
tracer = ExecutionTracer(engine="manager", phase=2)
metrics = MetricsCollector.get_instance()


@dataclass
class BrowserSession:
    """Represents an active browser session."""
    session_id: str
    engine: RuntimeEngine
    driver: BaseDriver
    context: Optional[BaseExecutionContext] = None
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    test_id: Optional[str] = None
    project_id: Optional[str] = None
    status: str = "active"  # "active", "closing", "closed", "error"

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at

    @property
    def idle_seconds(self) -> float:
        return time.time() - self.last_used


class BrowserSessionManager:
    """
    Manages the lifecycle of all browser sessions in the application.
    
    Responsibilities:
    - Create sessions (driver + context) via DriverFactory
    - Track active sessions for monitoring
    - Close individual sessions with cleanup
    - Shutdown all sessions on application exit
    - Enforce maximum concurrent session limits
    - Report session metrics
    
    Thread Safety:
    - Uses asyncio.Lock for session dict mutations
    - Safe for single-event-loop concurrent coroutines
    """

    _instance: Optional["BrowserSessionManager"] = None

    def __init__(self, max_sessions: int = 5) -> None:
        self._sessions: Dict[str, BrowserSession] = {}
        self._max_sessions = max_sessions
        self._lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        logger.info("BrowserSessionManager initialized (max_sessions=%d)", max_sessions)

    @classmethod
    def get_instance(cls, max_sessions: int = 5) -> "BrowserSessionManager":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(max_sessions=max_sessions)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (for testing)."""
        cls._instance = None

    @property
    def active_session_count(self) -> int:
        """Number of currently active sessions."""
        return len([s for s in self._sessions.values() if s.status == "active"])

    @property
    def is_at_capacity(self) -> bool:
        """Whether the maximum number of sessions has been reached."""
        return self.active_session_count >= self._max_sessions

    async def create_session(
        self,
        engine: Optional[RuntimeEngine] = None,
        config: Optional[BrowserConfig] = None,
        tenant_id: Optional[str] = None,
        test_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> str:
        """
        Create a new browser session.
        
        Args:
            engine: Engine to use (default: from FeatureFlags)
            config: Browser config (default: from FeatureFlags)
            tenant_id: For canary rollout
            test_id: Associated test ID for tracking
            project_id: Associated project ID for tracking
        
        Returns:
            Session ID (UUID string)
        
        Raises:
            RuntimeError: If at capacity or browser launch fails
        """
        async with self._lock:
            if self.is_at_capacity:
                raise RuntimeError(
                    f"Session limit reached ({self._max_sessions}). "
                    f"Close existing sessions before creating new ones."
                )

        # Import here to avoid circular dependency
        from backend.automation.driver_factory import DriverFactory

        # Resolve engine and config
        if engine is None:
            engine = FeatureFlags.resolve_engine(tenant_id)
        if config is None:
            config = BrowserConfig.from_feature_flags(test_id)

        session_id = str(uuid.uuid4())

        tracer.trace("session.create", {
            "session_id": session_id[:8],
            "engine": engine.value,
            "test_id": test_id or "none",
        })

        try:
            # Create and launch driver
            driver = await DriverFactory.create(
                engine=engine,
                config=config,
                tenant_id=tenant_id,
                auto_launch=True,
            )

            # Create execution context
            context = await driver.create_context()

            # Register session
            session = BrowserSession(
                session_id=session_id,
                engine=engine,
                driver=driver,
                context=context,
                test_id=test_id,
                project_id=project_id,
            )

            async with self._lock:
                self._sessions[session_id] = session

            metrics.increment("session.created", tags={"engine": engine.value})
            logger.info(
                "Session created: %s (engine=%s, test=%s)",
                session_id[:8],
                engine.value,
                test_id or "none",
            )

            return session_id

        except Exception as e:
            tracer.trace_error("session.create_failed", e, {
                "engine": engine.value,
                "test_id": test_id or "none",
            })
            raise

    async def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """Get a session by ID."""
        session = self._sessions.get(session_id)
        if session:
            session.last_used = time.time()
        return session

    async def get_context(self, session_id: str) -> Optional[BaseExecutionContext]:
        """Get the execution context for a session."""
        session = await self.get_session(session_id)
        return session.context if session else None

    async def get_driver(self, session_id: str) -> Optional[BaseDriver]:
        """Get the driver for a session."""
        session = await self.get_session(session_id)
        return session.driver if session else None

    async def close_session(self, session_id: str) -> Dict[str, Optional[str]]:
        """
        Close a session and release all resources.
        
        Returns:
            Artifact paths from context.close()
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.warning("Session not found: %s", session_id[:8])
            return {}

        tracer.trace("session.close", {
            "session_id": session_id[:8],
            "engine": session.engine.value,
            "age_seconds": round(session.age_seconds, 1),
        })

        session.status = "closing"
        artifacts: Dict[str, Optional[str]] = {}

        try:
            # Close context first (captures artifacts)
            if session.context and not session.context.is_closed:
                artifacts = await session.context.close()

            # Shutdown driver
            if session.driver:
                await session.driver.shutdown()

            session.status = "closed"
            metrics.increment("session.closed", tags={"engine": session.engine.value})

        except Exception as e:
            session.status = "error"
            tracer.trace_error("session.close_failed", e, {
                "session_id": session_id[:8],
            })
            logger.error("Error closing session %s: %s", session_id[:8], e)

        finally:
            async with self._lock:
                self._sessions.pop(session_id, None)

        return artifacts

    async def shutdown_all(self) -> None:
        """
        Shut down all active sessions.
        
        Called during application shutdown to ensure all browsers are closed.
        """
        logger.info("Shutting down all sessions (%d active)", self.active_session_count)
        self._shutdown_event.set()

        session_ids = list(self._sessions.keys())
        for sid in session_ids:
            try:
                await self.close_session(sid)
            except Exception as e:
                logger.error("Error closing session %s during shutdown: %s", sid[:8], e)

        logger.info("All sessions shut down")

    def list_sessions(self) -> list[Dict[str, Any]]:
        """List all sessions with their metadata (for diagnostics)."""
        return [
            {
                "session_id": s.session_id[:8] + "...",
                "engine": s.engine.value,
                "status": s.status,
                "test_id": s.test_id,
                "project_id": s.project_id,
                "age_seconds": round(s.age_seconds, 1),
                "idle_seconds": round(s.idle_seconds, 1),
            }
            for s in self._sessions.values()
        ]

    def summary(self) -> Dict[str, Any]:
        """Return a summary of session manager state."""
        return {
            "active_sessions": self.active_session_count,
            "max_sessions": self._max_sessions,
            "at_capacity": self.is_at_capacity,
            "sessions": self.list_sessions(),
        }
