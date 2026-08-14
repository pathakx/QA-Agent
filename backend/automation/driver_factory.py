"""
Driver Factory
===============

Creates Playwright browser driver instances.
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.automation.base_driver import BaseDriver
from backend.automation.config import BrowserConfig
from backend.automation.observability import (
    get_automation_logger,
    ExecutionTracer,
    MetricsCollector,
)

logger = get_automation_logger(
    "automation.driver_factory",
    engine="factory",
    phase=2,
    component="factory",
)
tracer = ExecutionTracer(engine="factory", phase=2)
metrics = MetricsCollector.get_instance()


class DriverFactory:
    """
    Factory for creating Playwright browser driver instances.
    """

    @classmethod
    async def create(
        cls,
        config: Optional[BrowserConfig] = None,
        tenant_id: Optional[str] = None,
        auto_launch: bool = True,
    ) -> BaseDriver:
        """
        Create a Playwright browser driver instance.
        
        Args:
            config: Browser configuration. If None, created from FeatureFlags.
            tenant_id: Optional tenant ID.
            auto_launch: If True, call driver.launch() before returning.
        
        Returns:
            Configured (and optionally launched) BaseDriver instance.
        """
        if config is None:
            config = BrowserConfig.from_feature_flags()

        tracer.trace("factory.create", {
            "engine": "playwright",
            "headless": config.headless,
            "browser_type": config.browser_type,
            "auto_launch": auto_launch,
        })

        try:
            from backend.automation.playwright_driver import PlaywrightDriver
            driver = PlaywrightDriver(config)
        except ImportError as e:
            error_msg = f"Playwright driver not available: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        metrics.increment("factory.create", tags={"engine": "playwright"})

        if auto_launch:
            try:
                await driver.launch()
                metrics.increment("factory.launch.success", tags={"engine": "playwright"})
            except Exception as e:
                metrics.increment("factory.launch.failure", tags={"engine": "playwright"})
                tracer.trace_error("factory.launch_failed", e, {"engine": "playwright"})
                try:
                    await driver.shutdown()
                except Exception:
                    pass
                raise RuntimeError(
                    f"Failed to launch playwright browser: {e}"
                ) from e

        return driver
