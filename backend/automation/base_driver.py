"""
Base Driver & Execution Result
===============================

Abstract base classes defining the contract that all browser automation
engines must implement. This is the foundation of the abstraction layer.

Design Decisions:
- BaseDriver manages browser-level lifecycle (launch/shutdown).
- BaseExecutionContext manages page-level lifecycle (navigate/interact/close).
- The split mirrors Playwright's Browser vs BrowserContext/Page separation,
  and is emulated on Selenium via a thin wrapper.
- All methods are async to support Playwright natively and Selenium via
  asyncio.to_thread().
- ExecutionResult is engine-agnostic — both engines produce the same output.

Lifecycle:
    driver = await DriverFactory.create("playwright")
    ctx = await driver.create_context(config)
    await ctx.navigate("https://example.com")
    await ctx.fill("#input", "value")
    artifacts = await ctx.close()
    await driver.shutdown()
"""

from __future__ import annotations

import platform
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ============================================================
# Execution Result (Engine-Agnostic)
# ============================================================

@dataclass
class ExecutionResult:
    """
    Engine-agnostic result of a test execution.
    
    Produced by both SeleniumDriver and PlaywrightDriver.
    Compatible with the existing execution_service.ExecutionResult
    for seamless migration (same fields, same semantics).
    """
    status: str                                  # "passed", "failed", "error", "timeout", "cancelled"
    logs: str                                    # Combined stdout/stderr or execution log
    duration: float                              # Wall-clock seconds
    error_message: Optional[str] = None          # Error details if status != "passed"
    screenshot_path: Optional[str] = None        # Path to failure screenshot
    video_path: Optional[str] = None             # Path to recorded video
    trace_path: Optional[str] = None             # Path to Playwright trace (PW only)
    browser: Optional[str] = None                # e.g., "chromium", "chrome"
    browser_version: Optional[str] = None        # e.g., "120.0.6099.109"
    os_info: Optional[str] = None                # e.g., "Windows 10.0.22631"
    engine: Optional[str] = None                 # "selenium" or "playwright"
    steps_executed: int = 0                       # Number of test steps completed
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extensible metadata

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        Convert to dict matching the format expected by existing DB update code
        in execution_api.py and batch_execution_service.py.
        """
        return {
            "status": self.status,
            "duration_seconds": self.duration,
            "logs": self.logs,
            "error_message": self.error_message,
            "screenshot_path": self.screenshot_path,
            "video_path": self.video_path,
            "browser": self.browser,
            "browser_version": self.browser_version,
            "os_info": self.os_info,
        }


# ============================================================
# Base Execution Context (Abstract)
# ============================================================

class BaseExecutionContext(ABC):
    """
    Abstract execution context — an isolated browser session.
    
    Maps to:
    - Playwright: BrowserContext + Page
    - Selenium: WebDriver instance (no true isolation)
    
    All interaction methods are async. Selenium implementations
    use asyncio.to_thread() internally.
    
    The context captures artifacts (screenshots, video, trace) and
    returns their paths on close().
    """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Return the engine identifier: 'playwright' or 'selenium'."""
        ...

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        """Whether this context has been closed."""
        ...

    # ── Navigation ──

    @abstractmethod
    async def navigate(self, url: str, wait_until: str = "load") -> None:
        """
        Navigate to a URL.
        
        Args:
            url: Target URL (supports http://, https://, file://)
            wait_until: Wait condition — "load", "domcontentloaded", "networkidle"
        """
        ...

    @abstractmethod
    async def reload(self) -> None:
        """Reload the current page."""
        ...

    @abstractmethod
    async def go_back(self) -> None:
        """Navigate back in browser history."""
        ...

    @abstractmethod
    async def current_url(self) -> str:
        """Return the current page URL."""
        ...

    @abstractmethod
    async def title(self) -> str:
        """Return the current page title."""
        ...

    # ── Element Interaction ──

    @abstractmethod
    async def fill(self, selector: str, value: str) -> None:
        """
        Clear and fill a text input.
        
        Args:
            selector: CSS selector, or Playwright locator string
            value: Text value to fill
        """
        ...

    @abstractmethod
    async def click(self, selector: str) -> None:
        """Click an element identified by selector."""
        ...

    @abstractmethod
    async def type_text(self, selector: str, text: str, delay_ms: int = 0) -> None:
        """
        Type text character by character (simulates real typing).
        
        Args:
            selector: Target element selector
            text: Text to type
            delay_ms: Delay between keystrokes in milliseconds
        """
        ...

    @abstractmethod
    async def select_option(self, selector: str, value: str) -> None:
        """Select an option from a <select> element by value."""
        ...

    @abstractmethod
    async def check(self, selector: str) -> None:
        """Check a checkbox or radio button."""
        ...

    @abstractmethod
    async def uncheck(self, selector: str) -> None:
        """Uncheck a checkbox."""
        ...

    # ── Element Queries ──

    @abstractmethod
    async def get_text(self, selector: str) -> str:
        """Get the text content of an element."""
        ...

    @abstractmethod
    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get an attribute value from an element."""
        ...

    @abstractmethod
    async def is_visible(self, selector: str) -> bool:
        """Check if an element is visible on the page."""
        ...

    @abstractmethod
    async def is_enabled(self, selector: str) -> bool:
        """Check if an element is enabled (not disabled)."""
        ...

    @abstractmethod
    async def element_count(self, selector: str) -> int:
        """Count elements matching the selector."""
        ...

    # ── Waiting ──

    @abstractmethod
    async def wait_for_selector(
        self,
        selector: str,
        state: str = "visible",
        timeout_ms: int = 10_000,
    ) -> None:
        """
        Wait for an element to reach the specified state.
        
        Args:
            selector: CSS selector
            state: "visible", "hidden", "attached", "detached"
            timeout_ms: Maximum wait time in milliseconds
        """
        ...

    @abstractmethod
    async def wait_for_navigation(self, timeout_ms: int = 30_000) -> None:
        """Wait for a navigation event to complete."""
        ...

    @abstractmethod
    async def wait_for_load_state(self, state: str = "load") -> None:
        """
        Wait for the page to reach a load state.
        
        Args:
            state: "load", "domcontentloaded", "networkidle"
        """
        ...

    # ── JavaScript ──

    @abstractmethod
    async def evaluate(self, expression: str) -> Any:
        """Execute JavaScript in the page context and return the result."""
        ...

    # ── Artifacts ──

    @abstractmethod
    async def screenshot(self, path: str, full_page: bool = False) -> str:
        """
        Capture a screenshot.
        
        Args:
            path: File path to save the screenshot
            full_page: If True, capture the full scrollable page
        
        Returns:
            The actual file path where the screenshot was saved
        """
        ...

    @abstractmethod
    async def page_content(self) -> str:
        """Return the full HTML content of the current page."""
        ...

    # ── Dialog Handling ──

    @abstractmethod
    async def setup_dialog_handler(self, accept: bool = True) -> None:
        """
        Set up automatic handling for JavaScript dialogs (alert/confirm/prompt).
        
        Args:
            accept: If True, accept dialogs. If False, dismiss them.
        """
        ...

    # ── Lifecycle ──

    @abstractmethod
    async def close(self) -> Dict[str, Optional[str]]:
        """
        Close this execution context and finalize artifacts.
        
        Returns:
            Dict with artifact paths:
            {
                "video_path": str or None,
                "trace_path": str or None,
                "screenshot_path": str or None,
            }
        """
        ...


# ============================================================
# Base Driver (Abstract)
# ============================================================

class BaseDriver(ABC):
    """
    Abstract browser driver — manages the browser-level lifecycle.
    
    Maps to:
    - Playwright: Playwright instance + Browser
    - Selenium: WebDriver (combined with context)
    
    A driver can create multiple execution contexts (Playwright)
    or just one (Selenium, which lacks true context isolation).
    """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Return the engine identifier: 'playwright' or 'selenium'."""
        ...

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Whether the browser is currently running."""
        ...

    @abstractmethod
    async def launch(self) -> None:
        """
        Launch the browser process.
        
        Configuration is passed via the constructor, not this method,
        to allow DriverFactory to configure drivers before launch.
        """
        ...

    @abstractmethod
    async def create_context(self) -> BaseExecutionContext:
        """
        Create a new isolated execution context.
        
        Each context has its own cookies, storage, and page.
        Playwright supports true isolation; Selenium shares state.
        """
        ...

    @abstractmethod
    async def get_browser_info(self) -> Dict[str, str]:
        """
        Return browser metadata.
        
        Returns:
            {"browser": "chromium", "version": "120.0", "os": "Windows 10.0"}
        """
        ...

    @abstractmethod
    async def is_healthy(self) -> bool:
        """
        Health check — verify the browser is responsive.
        
        Used by BrowserSessionManager for pool health monitoring.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shut down the browser and release all resources.
        
        Must be idempotent — safe to call multiple times.
        """
        ...

    async def get_platform_info(self) -> Dict[str, str]:
        """Return OS/platform information (non-abstract utility)."""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        }
