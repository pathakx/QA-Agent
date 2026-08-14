"""
Script Generation
================================

Generates Playwright scripts.
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.automation.observability import (
    get_automation_logger,
    ExecutionTracer,
    MetricsCollector,
)

logger = get_automation_logger(
    "automation.script_gen",
    engine="gen",
    phase=5,
    component="script_generation",
)
tracer = ExecutionTracer(engine="gen", phase=5)
metrics = MetricsCollector.get_instance()


def generate_script(
    testcase: dict,
    html_path: Optional[str] = None,
    collection_name: Optional[str] = None,
    engine: Optional[str] = None,
    project_id: Optional[str] = None,
) -> str:
    """
    Generate an automation script using Playwright.
    
    Args:
        testcase: Test case dict with test_id, scenario, steps, expected_result
        html_path: Path to the HTML file under test
        collection_name: Vector store collection for RAG
        engine: Ignored (always Playwright)
        project_id: Project ID
    
    Returns:
        Complete Python script string for Playwright
    """
    test_id = testcase.get("test_id", "unknown")

    tracer.trace("script_gen.start", {
        "engine": "playwright",
        "test_id": test_id,
    })

    from backend.services.playwright_service import generate_playwright_script

    try:
        script = generate_playwright_script(testcase, html_path, collection_name)
        metrics.increment("script_gen.success", tags={"engine": "playwright"})
        tracer.trace("script_gen.complete", {
            "engine": "playwright",
            "test_id": test_id,
            "lines": len(script.splitlines()),
        })
        return script

    except Exception as e:
        logger.error(
            "Playwright script generation failed for %s: %s",
            test_id, e,
        )
        tracer.trace("script_gen.error", {
            "test_id": test_id,
            "error": str(e),
        })
        raise


def get_prompt(
    testcase: dict,
    html_path: Optional[str] = None,
    collection_name: Optional[str] = None,
    engine: Optional[str] = None,
    project_id: Optional[str] = None,
) -> str:
    """
    Get the prompt that would be sent to the LLM.
    """
    from backend.services.playwright_service import build_playwright_prompt
    return build_playwright_prompt(testcase, html_path, collection_name)
