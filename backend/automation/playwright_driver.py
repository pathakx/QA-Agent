"""
Playwright Driver — Target Engine
===================================

Native async Playwright implementation of BaseDriver and BaseExecutionContext.
This is the target engine for the migration.

Design Decisions:
- Uses playwright.async_api exclusively — no sync API, no thread wrapping.
- Each PlaywrightExecutionContext wraps a BrowserContext + Page, providing
  true session isolation (separate cookies, storage, cache).
- Built-in video recording via context option (replaces OpenCV recorder).
- Built-in tracing via context.tracing API (no Selenium equivalent).
- Dialog handling via page.on("dialog") event listener (cleaner than try/except).
- Auto-waiting is inherent in all locator actions — no explicit waits needed
  in generated scripts.

Lazy Import:
- Playwright is imported lazily inside methods to avoid ImportError when
  only Selenium is installed (e.g., during early migration phases).
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
from typing import Any, Dict, Optional

from backend.automation.base_driver import BaseDriver, BaseExecutionContext
from backend.automation.config import BrowserConfig
from backend.automation.observability import (
    get_automation_logger,
    ExecutionTracer,
    timed_operation,
)

logger = get_automation_logger(
    "automation.playwright_driver",
    engine="playwright",
    phase=2,
    component="driver",
)
tracer = ExecutionTracer(engine="playwright", phase=2)


# ============================================================
# Playwright Execution Context
# ============================================================

class PlaywrightExecutionContext(BaseExecutionContext):
    """
    Playwright BrowserContext + Page wrapper implementing BaseExecutionContext.
    
    Features over Selenium:
    - True session isolation via BrowserContext
    - Built-in video recording
    - Built-in tracing (DOM snapshots + screenshots + network)
    - Auto-waiting on all locator actions
    - Dialog handling via event listeners
    - Accessibility tree access for self-healing
    """

    def __init__(
        self,
        context: Any,   # playwright.async_api.BrowserContext
        page: Any,       # playwright.async_api.Page
        config: BrowserConfig,
    ) -> None:
        self._context = context
        self._page = page
        self._config = config
        self._closed = False
        self._dialog_handler_set = False
        logger.debug("PlaywrightExecutionContext created")

    @property
    def engine_name(self) -> str:
        return "playwright"

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def page(self) -> Any:
        """Direct access to the Playwright Page for advanced usage."""
        return self._page

    @property
    def context(self) -> Any:
        """Direct access to the BrowserContext for advanced usage."""
        return self._context

    # ── Navigation ──

    async def navigate(self, url: str, wait_until: str = "load") -> None:
        tracer.trace("context.navigate", {"url": url, "wait_until": wait_until})
        await self._page.goto(url, wait_until=wait_until)

    async def reload(self) -> None:
        await self._page.reload()

    async def go_back(self) -> None:
        await self._page.go_back()

    async def current_url(self) -> str:
        return self._page.url

    async def title(self) -> str:
        return await self._page.title()

    # ── Element Interaction ──

    async def fill(self, selector: str, value: str) -> None:
        tracer.trace("context.fill", {"selector": selector})
        await self._page.fill(selector, value)

    async def click(self, selector: str) -> None:
        tracer.trace("context.click", {"selector": selector})
        await self._page.click(selector)

    async def type_text(self, selector: str, text: str, delay_ms: int = 0) -> None:
        tracer.trace("context.type_text", {"selector": selector, "length": len(text)})
        if delay_ms > 0:
            await self._page.type(selector, text, delay=delay_ms)
        else:
            await self._page.type(selector, text)

    async def select_option(self, selector: str, value: str) -> None:
        tracer.trace("context.select_option", {"selector": selector, "value": value})
        await self._page.select_option(selector, value)

    async def check(self, selector: str) -> None:
        await self._page.check(selector)

    async def uncheck(self, selector: str) -> None:
        await self._page.uncheck(selector)

    # ── Element Queries ──

    async def get_text(self, selector: str) -> str:
        result = await self._page.text_content(selector)
        return result or ""

    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        return await self._page.get_attribute(selector, attribute)

    async def is_visible(self, selector: str) -> bool:
        return await self._page.is_visible(selector)

    async def is_enabled(self, selector: str) -> bool:
        return await self._page.is_enabled(selector)

    async def element_count(self, selector: str) -> int:
        locator = self._page.locator(selector)
        return await locator.count()

    # ── Waiting ──

    async def wait_for_selector(
        self,
        selector: str,
        state: str = "visible",
        timeout_ms: int = 10_000,
    ) -> None:
        tracer.trace("context.wait_for_selector", {"selector": selector, "state": state})
        await self._page.wait_for_selector(selector, state=state, timeout=timeout_ms)

    async def wait_for_navigation(self, timeout_ms: int = 30_000) -> None:
        async with self._page.expect_navigation(timeout=timeout_ms):
            pass  # Caller should trigger navigation before this resolves

    async def wait_for_load_state(self, state: str = "load") -> None:
        await self._page.wait_for_load_state(state)

    # ── JavaScript ──

    async def evaluate(self, expression: str) -> Any:
        return await self._page.evaluate(expression)

    # ── Artifacts ──

    async def screenshot(self, path: str, full_page: bool = False) -> str:
        tracer.trace("context.screenshot", {"path": path, "full_page": full_page})
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        await self._page.screenshot(path=path, full_page=full_page)
        return path

    async def page_content(self) -> str:
        return await self._page.content()

    # ── Playwright-Specific Methods ──

    async def get_accessibility_tree(self) -> Optional[Dict[str, Any]]:
        """
        Get the accessibility tree of the current page.
        
        Used by self-healing to find elements by accessible role/name
        when CSS selectors break.
        
        Uses aria_snapshot() (Playwright v1.49+) with a fallback
        to JavaScript-based ARIA extraction for broader compatibility.
        
        Returns:
            Accessibility tree dict, or None if unavailable.
        """
        try:
            # Modern approach: use aria_snapshot() from locator API (v1.49+)
            root = self._page.locator(":root")
            snapshot_text = await root.aria_snapshot()
            return {"role": "WebArea", "snapshot": snapshot_text}
        except (AttributeError, Exception):
            pass

        # Fallback: extract ARIA info via JavaScript
        try:
            result = await self._page.evaluate("""() => {
                function getAriaTree(el, depth = 0) {
                    if (depth > 5) return null;
                    const role = el.getAttribute('role') || el.tagName.toLowerCase();
                    const name = el.getAttribute('aria-label') || el.textContent?.trim().slice(0, 50) || '';
                    const children = [];
                    for (const child of el.children) {
                        const c = getAriaTree(child, depth + 1);
                        if (c) children.push(c);
                    }
                    return { role, name, children: children.length > 0 ? children : undefined };
                }
                return getAriaTree(document.body);
            }""")
            return result
        except Exception as e:
            logger.warning("Failed to get accessibility tree: %s", e)
            return None

    async def get_locator(self, strategy: str, value: str) -> Any:
        """
        Get a Playwright locator using semantic strategy.
        
        Args:
            strategy: "role", "text", "label", "placeholder", "testid", "css"
            value: The locator value
        
        Returns:
            Playwright Locator object
        """
        if strategy == "role":
            return self._page.get_by_role(value)
        elif strategy == "text":
            return self._page.get_by_text(value)
        elif strategy == "label":
            return self._page.get_by_label(value)
        elif strategy == "placeholder":
            return self._page.get_by_placeholder(value)
        elif strategy == "testid":
            return self._page.get_by_test_id(value)
        else:
            return self._page.locator(value)

    # ── Dialog Handling ──

    async def setup_dialog_handler(self, accept: bool = True) -> None:
        if self._dialog_handler_set:
            return

        async def _handle_dialog(dialog: Any) -> None:
            tracer.trace("dialog.handled", {
                "type": dialog.type,
                "message": dialog.message[:100] if dialog.message else "",
                "action": "accept" if accept else "dismiss",
            })
            if accept:
                await dialog.accept()
            else:
                await dialog.dismiss()

        self._page.on("dialog", _handle_dialog)
        self._dialog_handler_set = True
        logger.debug("Dialog handler set: accept=%s", accept)

    # ── Lifecycle ──

    async def close(self) -> Dict[str, Optional[str]]:
        if self._closed:
            return {}

        tracer.trace("context.close")
        artifacts: Dict[str, Optional[str]] = {
            "video_path": None,
            "trace_path": None,
            "screenshot_path": None,
        }

        # Save trace if recording was enabled
        if self._config.record_trace and self._config.trace_dir:
            try:
                trace_path = os.path.join(self._config.trace_dir, "trace.zip")
                os.makedirs(self._config.trace_dir, exist_ok=True)
                await self._context.tracing.stop(path=trace_path)
                artifacts["trace_path"] = trace_path
                tracer.trace("artifact.trace_saved", {"path": trace_path})
            except Exception as e:
                logger.warning("Failed to save trace: %s", e)

        # Close context — this finalizes video recording
        await self._context.close()

        # Get video path after context close (video is finalized on close)
        if self._config.record_video:
            try:
                video = self._page.video
                if video:
                    video_path = await video.path()
                    artifacts["video_path"] = str(video_path)
                    tracer.trace("artifact.video_saved", {"path": str(video_path)})
            except Exception as e:
                logger.warning("Failed to get video path: %s", e)

        self._closed = True
        return artifacts


# ============================================================
# Playwright Driver
# ============================================================

class PlaywrightDriver(BaseDriver):
    """
    Playwright implementation of BaseDriver.
    
    Uses the async Playwright API for browser management.
    Supports multiple isolated BrowserContexts per browser instance.
    
    Features:
    - Native async — no thread wrapping needed
    - True context isolation via BrowserContext
    - Built-in video recording per context
    - Built-in tracing per context
    - Health checks via browser.is_connected()
    """

    def __init__(self, config: BrowserConfig) -> None:
        self._config = config
        self._playwright: Any = None   # playwright.async_api.Playwright
        self._browser: Any = None      # playwright.async_api.Browser
        self._launched = False
        logger.info(
            "PlaywrightDriver initialized (browser_type=%s, headless=%s)",
            config.browser_type,
            config.headless,
        )

    @property
    def engine_name(self) -> str:
        return "playwright"

    @property
    def is_running(self) -> bool:
        return self._browser is not None and self._browser.is_connected()

    @timed_operation("playwright.browser.launch", tags={"engine": "playwright"})
    async def launch(self) -> None:
        from playwright.async_api import async_playwright

        tracer.trace("browser.launch", {
            "engine": "playwright",
            "browser_type": self._config.browser_type,
            "headless": self._config.headless,
        })

        self._playwright = await async_playwright().start()

        # Resolve browser type
        browser_type_name = self._config.browser_type.lower()
        launcher = getattr(self._playwright, browser_type_name, None)
        if launcher is None:
            logger.warning(
                "Unknown browser type '%s', falling back to chromium",
                browser_type_name,
            )
            launcher = self._playwright.chromium

        # Build launch args
        launch_args = [
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-sandbox",
        ]
        launch_args.extend(self._config.extra_args)

        self._browser = await launcher.launch(
            headless=self._config.headless,
            args=launch_args,
        )

        self._launched = True
        logger.info(
            "Playwright browser launched (type=%s, version=%s)",
            browser_type_name,
            self._browser.version,
        )

    async def create_context(self) -> PlaywrightExecutionContext:
        if not self._launched or not self._browser:
            raise RuntimeError("Browser not launched. Call launch() first.")

        tracer.trace("context.create", {"engine": "playwright"})

        # Build context options
        context_options: Dict[str, Any] = {
            "viewport": {
                "width": self._config.viewport_width,
                "height": self._config.viewport_height,
            },
        }

        # Video recording
        if self._config.record_video and self._config.video_dir:
            os.makedirs(self._config.video_dir, exist_ok=True)
            context_options["record_video_dir"] = self._config.video_dir
            context_options["record_video_size"] = {
                "width": self._config.viewport_width,
                "height": self._config.viewport_height,
            }
            tracer.trace("context.video_enabled", {"dir": self._config.video_dir})

        # Create context
        context = await self._browser.new_context(**context_options)

        # Start tracing if enabled
        if self._config.record_trace and self._config.trace_dir:
            os.makedirs(self._config.trace_dir, exist_ok=True)
            await context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True,
            )
            tracer.trace("context.tracing_enabled", {"dir": self._config.trace_dir})

        # Create page
        page = await context.new_page()
        page.set_default_timeout(self._config.timeout_ms)
        page.set_default_navigation_timeout(self._config.navigation_timeout_ms)

        return PlaywrightExecutionContext(
            context=context,
            page=page,
            config=self._config,
        )

    async def get_browser_info(self) -> Dict[str, str]:
        if not self._browser:
            return {"browser": "unknown", "version": "unknown", "os": "unknown"}

        return {
            "browser": self._browser.browser_type.name,
            "version": self._browser.version,
            "os": f"{platform.system()} {platform.version()}",
        }

    async def is_healthy(self) -> bool:
        if not self._browser or not self._browser.is_connected():
            return False

        try:
            # Quick health check: create and immediately close a context
            ctx = await self._browser.new_context()
            page = await ctx.new_page()
            await page.goto("about:blank")
            await ctx.close()
            return True
        except Exception as e:
            logger.warning("Health check failed: %s", e)
            return False

    async def shutdown(self) -> None:
        tracer.trace("browser.shutdown", {"engine": "playwright"})

        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning("Error closing browser: %s", e)
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning("Error stopping playwright: %s", e)
            self._playwright = None

        self._launched = False
        logger.info("Playwright browser shut down")
