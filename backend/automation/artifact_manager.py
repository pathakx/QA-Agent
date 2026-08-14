"""
Artifact Manager
=================

Manages test execution artifacts: screenshots, videos, and traces.
Provides a unified interface for artifact capture, storage, and cleanup
regardless of the underlying browser engine.

Design Decisions:
- Engine-agnostic — works with both Selenium and Playwright contexts.
- Directory structure: test_results/{test_id}/{artifact_type}/{timestamp}.ext
- Screenshots: captured by the context, managed by this class.
- Videos: Playwright records natively; Selenium uses external recorder (legacy).
- Traces: Playwright-only; stored as .zip files.
- Cleanup: configurable retention policy (default 7 days).
- Thread-safe path generation via timestamps.
"""

from __future__ import annotations

import os
import time
import shutil
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from pathlib import Path

from backend.automation.base_driver import BaseExecutionContext
from backend.automation.observability import (
    get_automation_logger,
    ExecutionTracer,
    MetricsCollector,
)

logger = get_automation_logger(
    "automation.artifact_manager",
    engine="artifacts",
    phase=2,
    component="artifacts",
)
tracer = ExecutionTracer(engine="artifacts", phase=2)
metrics = MetricsCollector.get_instance()


@dataclass
class ArtifactPaths:
    """
    Container for all artifact paths related to a test execution.
    
    Populated incrementally as artifacts are captured during execution.
    """
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    trace_path: Optional[str] = None
    additional: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dict for DB storage."""
        result = {
            "screenshot_path": self.screenshot_path,
            "video_path": self.video_path,
            "trace_path": self.trace_path,
        }
        result.update(self.additional)
        return result

    @property
    def has_any(self) -> bool:
        """Whether any artifacts have been captured."""
        return bool(self.screenshot_path or self.video_path or self.trace_path)


class ArtifactManager:
    """
    Manages test execution artifacts across both engines.
    
    Provides:
    - Directory structure management
    - Screenshot capture (via execution context)
    - Video path resolution (from context close)
    - Trace path resolution (from context close)
    - Artifact cleanup (retention policy)
    - Artifact listing for API responses
    
    Usage:
        manager = ArtifactManager(base_dir="test_results")
        
        # Get directories for a test
        dirs = manager.get_artifact_dirs("TC-001")
        
        # Capture screenshot
        path = await manager.capture_screenshot(context, "TC-001", suffix="failure")
        
        # Merge artifacts from context.close()
        artifacts = manager.merge_context_artifacts("TC-001", context_artifacts)
        
        # Cleanup old artifacts
        manager.cleanup(max_age_days=7)
    """

    DEFAULT_BASE_DIR = "test_results"

    def __init__(self, base_dir: Optional[str] = None) -> None:
        self._base_dir = base_dir or self.DEFAULT_BASE_DIR
        logger.info("ArtifactManager initialized (base_dir=%s)", self._base_dir)

    @property
    def base_dir(self) -> str:
        return self._base_dir

    # ── Directory Management ──

    def get_test_dir(self, test_id: str) -> str:
        """Get the root artifact directory for a test."""
        path = os.path.join(self._base_dir, test_id)
        os.makedirs(path, exist_ok=True)
        return path

    def get_screenshot_dir(self, test_id: str) -> str:
        """Get the screenshot directory for a test."""
        path = os.path.join(self._base_dir, test_id, "screenshots")
        os.makedirs(path, exist_ok=True)
        return path

    def get_video_dir(self, test_id: str) -> str:
        """Get the video directory for a test."""
        path = os.path.join(self._base_dir, test_id, "videos")
        os.makedirs(path, exist_ok=True)
        return path

    def get_trace_dir(self, test_id: str) -> str:
        """Get the trace directory for a test."""
        path = os.path.join(self._base_dir, test_id, "traces")
        os.makedirs(path, exist_ok=True)
        return path

    def get_artifact_dirs(self, test_id: str) -> Dict[str, str]:
        """
        Get all artifact directories for a test.
        Creates directories if they don't exist.
        
        Returns:
            {"screenshots": path, "videos": path, "traces": path}
        """
        return {
            "screenshots": self.get_screenshot_dir(test_id),
            "videos": self.get_video_dir(test_id),
            "traces": self.get_trace_dir(test_id),
        }

    # ── Screenshot Capture ──

    async def capture_screenshot(
        self,
        context: BaseExecutionContext,
        test_id: str,
        suffix: str = "capture",
        full_page: bool = True,
    ) -> Optional[str]:
        """
        Capture a screenshot using the execution context.
        
        Args:
            context: Active execution context (Selenium or Playwright)
            test_id: Test ID for directory organization
            suffix: Filename suffix (e.g., "failure", "step_3", "final")
            full_page: Whether to capture the full scrollable page
        
        Returns:
            Absolute file path to the saved screenshot, or None on failure.
        """
        try:
            screenshot_dir = self.get_screenshot_dir(test_id)
            timestamp = int(time.time() * 1000)  # Milliseconds for uniqueness
            filename = f"{suffix}_{timestamp}.png"
            filepath = os.path.abspath(os.path.join(screenshot_dir, filename))

            await context.screenshot(filepath, full_page=full_page)

            tracer.trace("artifact.screenshot_captured", {
                "test_id": test_id,
                "path": filepath,
                "suffix": suffix,
            })
            metrics.increment("artifact.screenshot", tags={"status": "success"})

            return filepath

        except Exception as e:
            logger.warning(
                "Failed to capture screenshot for %s: %s", test_id, e
            )
            metrics.increment("artifact.screenshot", tags={"status": "failure"})
            return None

    # ── Artifact Merging ──

    def merge_context_artifacts(
        self,
        test_id: str,
        context_artifacts: Dict[str, Optional[str]],
        screenshot_path: Optional[str] = None,
    ) -> ArtifactPaths:
        """
        Merge artifacts from context.close() with any separately captured ones.
        
        Args:
            test_id: Test ID
            context_artifacts: Dict from context.close() with video_path, trace_path
            screenshot_path: Separately captured screenshot path
        
        Returns:
            Unified ArtifactPaths object
        """
        artifacts = ArtifactPaths(
            screenshot_path=screenshot_path,
            video_path=context_artifacts.get("video_path"),
            trace_path=context_artifacts.get("trace_path"),
        )

        if artifacts.has_any:
            tracer.trace("artifact.merged", {
                "test_id": test_id,
                "has_screenshot": bool(artifacts.screenshot_path),
                "has_video": bool(artifacts.video_path),
                "has_trace": bool(artifacts.trace_path),
            })

        return artifacts

    # ── Artifact Listing ──

    def list_artifacts(self, test_id: str) -> Dict[str, List[str]]:
        """
        List all artifacts for a test.
        
        Returns:
            {"screenshots": [...], "videos": [...], "traces": [...]}
        """
        result: Dict[str, List[str]] = {
            "screenshots": [],
            "videos": [],
            "traces": [],
        }

        test_dir = os.path.join(self._base_dir, test_id)
        if not os.path.exists(test_dir):
            return result

        for artifact_type in ["screenshots", "videos", "traces"]:
            type_dir = os.path.join(test_dir, artifact_type)
            if os.path.exists(type_dir):
                result[artifact_type] = sorted(os.listdir(type_dir))

        return result

    # ── Cleanup ──

    def cleanup(self, max_age_days: int = 7) -> Dict[str, int]:
        """
        Remove artifacts older than max_age_days.
        
        Returns:
            {"removed_dirs": count, "freed_bytes": bytes}
        """
        cutoff = time.time() - (max_age_days * 86400)
        removed_count = 0
        freed_bytes = 0

        if not os.path.exists(self._base_dir):
            return {"removed_dirs": 0, "freed_bytes": 0}

        for test_dir_name in os.listdir(self._base_dir):
            test_dir_path = os.path.join(self._base_dir, test_dir_name)
            if not os.path.isdir(test_dir_path):
                continue

            # Check modification time
            if os.path.getmtime(test_dir_path) < cutoff:
                try:
                    dir_size = self._get_dir_size(test_dir_path)
                    shutil.rmtree(test_dir_path, ignore_errors=True)
                    removed_count += 1
                    freed_bytes += dir_size
                except Exception as e:
                    logger.warning(
                        "Failed to remove artifact dir %s: %s",
                        test_dir_name,
                        e,
                    )

        if removed_count > 0:
            tracer.trace("artifact.cleanup", {
                "removed_dirs": removed_count,
                "freed_mb": round(freed_bytes / (1024 * 1024), 2),
                "max_age_days": max_age_days,
            })

        return {"removed_dirs": removed_count, "freed_bytes": freed_bytes}

    def cleanup_test(self, test_id: str) -> bool:
        """Remove all artifacts for a specific test."""
        test_dir = os.path.join(self._base_dir, test_id)
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)
            tracer.trace("artifact.cleanup_test", {"test_id": test_id})
            return True
        return False

    # ── Utilities ──

    @staticmethod
    def _get_dir_size(path: str) -> int:
        """Get total size of a directory in bytes."""
        total = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
        return total

    def summary(self) -> Dict[str, Any]:
        """Return a summary of artifact storage for diagnostics."""
        if not os.path.exists(self._base_dir):
            return {"base_dir": self._base_dir, "test_count": 0, "total_size_mb": 0}

        test_dirs = [
            d for d in os.listdir(self._base_dir)
            if os.path.isdir(os.path.join(self._base_dir, d))
        ]

        total_size = self._get_dir_size(self._base_dir)

        return {
            "base_dir": os.path.abspath(self._base_dir),
            "test_count": len(test_dirs),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
