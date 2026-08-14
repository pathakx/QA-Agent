"""
Playwright Runtime Manager
============================

Manages the Playwright runtime lifecycle at the application level.
Integrates with FastAPI lifespan events for clean startup/shutdown.

Design Decisions:
- Singleton pattern — one runtime per process.
- Lazy initialization — Playwright is started on first use, not at import.
- Integrates with BrowserSessionManager for session cleanup on shutdown.
- Provides health check method for monitoring endpoints.
- Manages browser binary validation on startup.

Usage:
    # In FastAPI lifespan:
    @asynccontextmanager
    async def lifespan(app):
        await PlaywrightRuntime.get_instance().startup()
        yield
        await PlaywrightRuntime.get_instance().shutdown()
    
    # In execution code:
    runtime = PlaywrightRuntime.get_instance()
    if runtime.is_ready:
        driver = await DriverFactory.create(engine=RuntimeEngine.PLAYWRIGHT)
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from backend.automation.config import RuntimeEngine, FeatureFlags, BrowserConfig
from backend.automation.observability import (
    get_automation_logger,
    ExecutionTracer,
    MetricsCollector,
)

logger = get_automation_logger(
    "automation.runtime",
    engine="playwright",
    phase=3,
    component="runtime",
)
tracer = ExecutionTracer(engine="playwright", phase=3)
metrics = MetricsCollector.get_instance()


class PlaywrightRuntime:
    """
    Application-level Playwright runtime manager.
    
    Responsibilities:
    - Validate Playwright installation and browser binaries
    - Start/stop the Playwright async runtime
    - Provide health checks for readiness probes
    - Integrate with FastAPI lifespan for graceful shutdown
    - Manage runtime-level configuration
    
    This is NOT a browser pool — it manages the Playwright process itself.
    Browser pooling is handled by BrowserSessionManager (Phase 2) and
    will be enhanced in Phase 7.
    """

    _instance: Optional["PlaywrightRuntime"] = None

    def __init__(self) -> None:
        self._playwright: Any = None         # playwright.async_api.Playwright
        self._is_ready = False
        self._browser_installed = False
        self._playwright_version: Optional[str] = None
        self._chromium_path: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "PlaywrightRuntime":
        """Get or create the singleton runtime instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    @property
    def is_ready(self) -> bool:
        """Whether the runtime is initialized and browsers are available."""
        return self._is_ready

    @property
    def playwright_version(self) -> Optional[str]:
        """Installed Playwright version."""
        return self._playwright_version

    # ── Lifecycle ──

    async def startup(self) -> bool:
        """
        Initialize the Playwright runtime.
        
        Steps:
        1. Validate Playwright is installed
        2. Check browser binaries are available
        3. Perform a smoke test (launch + close browser)
        4. Mark runtime as ready
        
        Returns:
            True if runtime is ready, False if initialization failed.
        """
        logger.info("Starting Playwright runtime initialization...")

        # Step 1: Check Playwright package
        if not self._check_playwright_installed():
            logger.warning("Playwright package not installed. Runtime not available.")
            return False

        # Step 2: Check browser binaries
        if not self._check_browser_binaries():
            logger.warning(
                "Playwright browser binaries not found. "
                "Run: python -m playwright install chromium"
            )
            return False

        # Step 3: Smoke test
        smoke_ok = await self._smoke_test()
        if not smoke_ok:
            logger.error("Playwright smoke test failed. Runtime not available.")
            return False

        self._is_ready = True
        tracer.trace("runtime.startup", {
            "version": self._playwright_version or "unknown",
            "browser_installed": self._browser_installed,
        })
        logger.info(
            "Playwright runtime ready (version=%s)",
            self._playwright_version,
        )
        metrics.increment("runtime.startup.success")
        return True

    async def shutdown(self) -> None:
        """
        Shut down the Playwright runtime.
        
        Also shuts down all active browser sessions via BrowserSessionManager.
        """
        logger.info("Shutting down Playwright runtime...")

        # Shutdown all active sessions
        try:
            from backend.automation.browser_session import BrowserSessionManager
            manager = BrowserSessionManager.get_instance()
            await manager.shutdown_all()
        except Exception as e:
            logger.warning("Error shutting down browser sessions: %s", e)

        self._is_ready = False
        tracer.trace("runtime.shutdown")
        metrics.increment("runtime.shutdown")
        logger.info("Playwright runtime shut down")

    # ── Health Check ──

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the Playwright runtime.
        
        Returns:
            Dict with health status, version info, and diagnostics.
        """
        health: Dict[str, Any] = {
            "status": "healthy" if self._is_ready else "unavailable",
            "playwright_installed": self._playwright_version is not None,
            "playwright_version": self._playwright_version,
            "browser_binaries_installed": self._browser_installed,
            "feature_flags": {
                "enabled": FeatureFlags.is_playwright_enabled(),
                "engine": FeatureFlags.get_engine().value,
                "rollout_pct": FeatureFlags.get_rollout_percentage(),
            },
        }

        # If runtime is ready, do a quick browser health check
        if self._is_ready:
            try:
                from backend.automation.driver_factory import DriverFactory
                config = BrowserConfig(headless=True)
                driver = await DriverFactory.create(
                    engine=RuntimeEngine.PLAYWRIGHT,
                    config=config,
                    auto_launch=True,
                )
                browser_info = await driver.get_browser_info()
                is_healthy = await driver.is_healthy()
                await driver.shutdown()

                health["browser_health"] = is_healthy
                health["browser_info"] = browser_info
            except Exception as e:
                health["browser_health"] = False
                health["browser_error"] = str(e)

        # Add session manager stats
        try:
            from backend.automation.browser_session import BrowserSessionManager
            manager = BrowserSessionManager.get_instance()
            health["sessions"] = manager.summary()
        except Exception:
            pass

        # Add metrics summary
        health["metrics"] = metrics.summary()

        return health

    # ── Validation ──

    def _check_playwright_installed(self) -> bool:
        """Check if the Playwright Python package is installed."""
        try:
            import playwright
            self._playwright_version = getattr(playwright, "__version__", "unknown")
            logger.info("Playwright package found (version=%s)", self._playwright_version)
            return True
        except ImportError:
            logger.warning("Playwright package not installed")
            return False

    def _check_browser_binaries(self) -> bool:
        """
        Check if Playwright browser binaries are downloaded.
        
        Playwright stores browsers in a platform-specific cache directory.
        We check if the chromium directory exists.
        """
        try:
            # Playwright stores browsers in PLAYWRIGHT_BROWSERS_PATH or default location
            browsers_path = os.environ.get(
                "PLAYWRIGHT_BROWSERS_PATH",
                os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright")
            )

            if os.path.exists(browsers_path):
                # Look for any chromium directory
                entries = os.listdir(browsers_path)
                chromium_dirs = [e for e in entries if "chromium" in e.lower()]
                if chromium_dirs:
                    self._browser_installed = True
                    self._chromium_path = os.path.join(browsers_path, chromium_dirs[0])
                    logger.info("Chromium binaries found at: %s", self._chromium_path)
                    return True

            logger.warning("No Chromium binaries found in %s", browsers_path)
            self._browser_installed = False
            return False

        except Exception as e:
            logger.warning("Error checking browser binaries: %s", e)
            return False

    async def _smoke_test(self) -> bool:
        """
        Perform a quick smoke test: launch browser, open blank page, close.
        
        This validates that the browser can actually start in this environment.
        """
        try:
            from playwright.async_api import async_playwright

            logger.info("Running Playwright smoke test...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-dev-shm-usage", "--disable-gpu", "--no-sandbox"],
                )
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto("about:blank")
                title = await page.title()
                await context.close()
                await browser.close()

            logger.info("Smoke test passed (title='%s')", title)
            return True

        except Exception as e:
            logger.error("Smoke test failed: %s", e)
            tracer.trace_error("runtime.smoke_test_failed", e)
            return False

    def summary(self) -> Dict[str, Any]:
        """Return runtime status for diagnostics."""
        return {
            "is_ready": self._is_ready,
            "playwright_version": self._playwright_version,
            "browser_installed": self._browser_installed,
            "chromium_path": self._chromium_path,
        }
