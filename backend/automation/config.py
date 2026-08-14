"""
Playwright Engine Configuration & Feature Flags
====================================

Centralizes all configuration including:
- Feature flags 
- Browser configuration dataclasses
- Execution configuration

Design Decisions:
- Feature flags are environment-driven, not DB-driven, for simplicity.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger("automation.config")

# ============================================================
# Feature Flags
# ============================================================

class FeatureFlags:
    """
    Feature flags evaluated from environment variables.
    
    Environment Variables:
        PLAYWRIGHT_VIDEO        : "true" | "false"
        PLAYWRIGHT_TRACING      : "true" | "false"
        PLAYWRIGHT_BROWSER_POOL : "true" | "false"
        PLAYWRIGHT_SELF_HEALING : "true" | "false"
        MIGRATION_DRY_RUN       : "true" | "false"
    """

    @staticmethod
    def _env_bool(key: str, default: bool = False) -> bool:
        """Read a boolean from environment."""
        return os.getenv(key, str(default)).lower().strip() in ("true", "1", "yes")

    # --- Feature-Level Flags ---

    @classmethod
    def is_video_enabled(cls) -> bool:
        """Enable Playwright built-in video recording."""
        return cls._env_bool("PLAYWRIGHT_VIDEO", default=False)

    @classmethod
    def is_tracing_enabled(cls) -> bool:
        """Enable Playwright tracing (screenshots + DOM snapshots)."""
        return cls._env_bool("PLAYWRIGHT_TRACING", default=False)

    @classmethod
    def is_browser_pool_enabled(cls) -> bool:
        """Enable browser instance pooling and reuse."""
        return cls._env_bool("PLAYWRIGHT_BROWSER_POOL", default=False)

    @classmethod
    def is_self_healing_v2_enabled(cls) -> bool:
        """Enable Playwright-enhanced self-healing (DOM snapshot + a11y tree)."""
        return cls._env_bool("PLAYWRIGHT_SELF_HEALING", default=False)

    @classmethod
    def is_dry_run(cls) -> bool:
        """Dry run mode: log what would happen without executing."""
        return cls._env_bool("MIGRATION_DRY_RUN", default=False)

    @classmethod
    def summary(cls) -> Dict[str, Any]:
        """Return a summary of all feature flags for diagnostics."""
        return {
            "video_enabled": cls.is_video_enabled(),
            "tracing_enabled": cls.is_tracing_enabled(),
            "browser_pool_enabled": cls.is_browser_pool_enabled(),
            "self_healing_v2_enabled": cls.is_self_healing_v2_enabled(),
            "dry_run": cls.is_dry_run(),
        }


# ============================================================
# Browser Configuration
# ============================================================

@dataclass
class BrowserConfig:
    """
    Browser configuration for Playwright.
    """
    headless: bool = True
    browser_type: str = "chromium"          # chromium, firefox, webkit (PW)
    viewport_width: int = 1280
    viewport_height: int = 720
    timeout_ms: int = 30_000                # Default action timeout
    navigation_timeout_ms: int = 30_000     # Page load timeout
    record_video: bool = False
    record_trace: bool = False
    video_dir: Optional[str] = None         # Directory for video artifacts
    trace_dir: Optional[str] = None         # Directory for trace artifacts
    screenshot_on_failure: bool = True
    extra_args: List[str] = field(default_factory=list)
    extra_env: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_feature_flags(cls, test_id: Optional[str] = None) -> "BrowserConfig":
        """
        Create a BrowserConfig populated from current feature flags.
        
        Args:
            test_id: Optional test ID used for artifact directory paths.
        """
        video_dir = f"test_results/{test_id}/videos" if test_id else None
        trace_dir = f"test_results/{test_id}/traces" if test_id else None

        return cls(
            headless=True,
            record_video=FeatureFlags.is_video_enabled(),
            record_trace=FeatureFlags.is_tracing_enabled(),
            video_dir=video_dir,
            trace_dir=trace_dir,
            extra_args=["--disable-dev-shm-usage", "--disable-gpu", "--no-sandbox"],
        )


# ============================================================
# Execution Configuration
# ============================================================

@dataclass
class ExecutionConfig:
    """
    Configuration for a single test execution.
    
    Combines browser config with execution-level settings like
    timeouts, retries, and artifact preferences.
    """
    browser_config: BrowserConfig = field(default_factory=BrowserConfig)
    max_retries: int = 0
    execution_timeout_seconds: int = 60
    capture_screenshot_on_pass: bool = False
    capture_screenshot_on_fail: bool = True
    capture_video: bool = False
    capture_trace: bool = False
    test_id: Optional[str] = None
    project_id: Optional[str] = None
    tenant_id: Optional[str] = None

    @classmethod
    def from_feature_flags(
        cls,
        test_id: Optional[str] = None,
        project_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        max_retries: int = 0,
    ) -> "ExecutionConfig":
        """
        Create an ExecutionConfig from current feature flags.
        """
        browser_config = BrowserConfig.from_feature_flags(test_id)

        return cls(
            browser_config=browser_config,
            max_retries=max_retries,
            test_id=test_id,
            project_id=project_id,
            tenant_id=tenant_id,
            capture_video=FeatureFlags.is_video_enabled(),
            capture_trace=FeatureFlags.is_tracing_enabled(),
        )
