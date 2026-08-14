"""
Automation Abstraction Layer
============================

Provides engine-agnostic browser automation for the QA Agent platform.
Supports Selenium (legacy) and Playwright (target) via a unified interface.

Architecture:
    DriverFactory → BaseDriver → {PlaywrightDriver, SeleniumDriver}
    BrowserPoolManager → BrowserContext → ExecutionContext → ArtifactManager

Feature Flags:
    BROWSER_ENGINE           : "selenium" | "playwright" (default: "selenium")
    PLAYWRIGHT_ENABLED       : true/false — master kill switch
    PLAYWRIGHT_ROLLOUT_PCT   : 0-100 — canary rollout percentage

Usage:
    from backend.automation.driver_factory import DriverFactory
    driver = await DriverFactory.create()
"""

__version__ = "0.1.0"
__migration_phase__ = 1  # Current migration phase
