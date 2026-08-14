"""
Migration Ledger
================

Tracks the state of the Selenium → Playwright migration.
Provides a machine-readable record of:
- Completed phases and tasks
- Modified files per phase
- Known risks and mitigations
- Pending work
- Rollback instructions

The ledger is a living document updated as each phase completes.
It is also queryable at runtime via the /api/migration/status endpoint (future).

Design Decision:
- The ledger is a Python data structure, not a database table,
  because it tracks code-level migration state, not user data.
- Each phase entry is frozen once completed and should not be modified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class PhaseStatus(str, Enum):
    """Status of a migration phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


@dataclass
class RiskEntry:
    """A known risk with its mitigation strategy."""
    risk_id: str
    description: str
    severity: str               # "low", "medium", "high", "critical"
    mitigation: str
    status: str = "open"        # "open", "mitigated", "accepted"


@dataclass
class FileChange:
    """Record of a file created or modified in a phase."""
    file_path: str
    change_type: str            # "created", "modified", "deprecated", "deleted"
    description: str


@dataclass
class PhaseEntry:
    """Record for a single migration phase."""
    phase_number: int
    name: str
    status: PhaseStatus
    objectives: List[str]
    files_changed: List[FileChange] = field(default_factory=list)
    risks: List[RiskEntry] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    rollback_notes: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: str = ""


# ============================================================
# The Migration Ledger
# ============================================================

MIGRATION_LEDGER: List[PhaseEntry] = [

    # ----------------------------------------------------------
    # PHASE 1 — Foundation & Governance
    # ----------------------------------------------------------
    PhaseEntry(
        phase_number=1,
        name="Foundation & Governance",
        status=PhaseStatus.COMPLETED,
        started_at=datetime.utcnow().isoformat(),
        objectives=[
            "Create automation package structure",
            "Implement RuntimeEngine enum",
            "Implement FeatureFlags with canary rollout",
            "Implement BrowserConfig and ExecutionConfig",
            "Implement structured logging and observability",
            "Implement MetricsCollector for migration tracking",
            "Implement ExecutionTracer for lifecycle events",
            "Create migration ledger",
            "Dependency audit — add playwright to requirements",
            "Update core config with migration settings",
        ],
        files_changed=[
            FileChange(
                "backend/automation/__init__.py",
                "created",
                "Package init with version and migration phase"
            ),
            FileChange(
                "backend/automation/config.py",
                "created",
                "RuntimeEngine enum, FeatureFlags, BrowserConfig, ExecutionConfig"
            ),
            FileChange(
                "backend/automation/observability.py",
                "created",
                "Structured logging, MetricsCollector, ExecutionTracer, timed_operation decorator"
            ),
            FileChange(
                "backend/automation/migration_ledger.py",
                "created",
                "Migration ledger data structure and phase tracking"
            ),
            FileChange(
                "backend/core/config.py",
                "modified",
                "Added BROWSER_ENGINE, PLAYWRIGHT_ENABLED, and related settings"
            ),
            FileChange(
                "requirements.txt",
                "modified",
                "Added playwright dependency (install separately with: playwright install chromium)"
            ),
        ],
        risks=[
            RiskEntry(
                "R-001",
                "Playwright import fails if not installed",
                "low",
                "All Playwright imports are lazy (inside functions). System works with Selenium-only.",
                "mitigated"
            ),
            RiskEntry(
                "R-002",
                "Feature flags misconfigured in production",
                "medium",
                "All flags default to Selenium behavior. Playwright requires explicit opt-in.",
                "mitigated"
            ),
            RiskEntry(
                "R-003",
                "Logging overhead in hot paths",
                "low",
                "Logging is INFO-level by default. DEBUG can be enabled per-module.",
                "accepted"
            ),
        ],
        pending_tasks=[],
        rollback_notes=(
            "Delete backend/automation/ directory. "
            "Revert backend/core/config.py to remove new settings. "
            "Remove playwright from requirements.txt. "
            "System returns to pre-migration state with zero impact."
        ),
        notes="Phase 1 is purely additive. No existing code is modified in behavior."
    ),

    # ----------------------------------------------------------
    # PHASE 2 — Automation Abstraction Layer
    # ----------------------------------------------------------
    PhaseEntry(
        phase_number=2,
        name="Automation Abstraction Layer",
        status=PhaseStatus.COMPLETED,
        started_at=datetime.utcnow().isoformat(),
        objectives=[
            "Implement BaseDriver abstract base class",
            "Implement BaseExecutionContext abstract base class",
            "Implement ExecutionResult engine-agnostic dataclass",
            "Implement SeleniumDriver wrapping existing behavior",
            "Implement SeleniumExecutionContext with asyncio.to_thread",
            "Implement PlaywrightDriver with native async API",
            "Implement PlaywrightExecutionContext with context isolation",
            "Implement DriverFactory with registry pattern and auto-registration",
            "Implement fallback engine resolution in DriverFactory",
            "Implement BrowserSessionManager with session tracking",
            "Implement ArtifactManager with directory management and cleanup",
        ],
        files_changed=[
            FileChange(
                "backend/automation/base_driver.py",
                "created",
                "BaseDriver ABC, BaseExecutionContext ABC, ExecutionResult dataclass"
            ),
            FileChange(
                "backend/automation/selenium_driver.py",
                "created",
                "SeleniumDriver + SeleniumExecutionContext — async wrapper over sync Selenium"
            ),
            FileChange(
                "backend/automation/playwright_driver.py",
                "created",
                "PlaywrightDriver + PlaywrightExecutionContext — native async Playwright"
            ),
            FileChange(
                "backend/automation/driver_factory.py",
                "created",
                "DriverFactory with registry, auto-registration, and fallback"
            ),
            FileChange(
                "backend/automation/browser_session.py",
                "created",
                "BrowserSessionManager singleton — session tracking and cleanup"
            ),
            FileChange(
                "backend/automation/artifact_manager.py",
                "created",
                "ArtifactManager — screenshots, videos, traces, cleanup"
            ),
        ],
        risks=[
            RiskEntry(
                "R-004",
                "SeleniumDriver wrapper introduces overhead",
                "low",
                "Wrapper uses asyncio.to_thread() — same as current execution_service.py",
                "mitigated"
            ),
            RiskEntry(
                "R-005",
                "Playwright lazy imports may mask installation issues",
                "low",
                "DriverFactory.summary() shows which engines are registered at startup",
                "mitigated"
            ),
        ],
        pending_tasks=[],
        rollback_notes=(
            "Delete Phase 2 files from backend/automation/ "
            "(base_driver.py, selenium_driver.py, playwright_driver.py, "
            "driver_factory.py, browser_session.py, artifact_manager.py). "
            "No existing code was modified. System works identically."
        ),
        notes="Phase 2 is purely additive. No existing code is modified. All 7 new modules validated."
    ),

    # Phases 3-11 are tracked but not yet populated with details.
    # They will be filled in as each preceding phase completes.

    PhaseEntry(
        phase_number=3,
        name="Playwright Prototype Engine",
        status=PhaseStatus.COMPLETED,
        started_at=datetime.utcnow().isoformat(),
        objectives=[
            "Install Playwright and Chromium browser binaries",
            "Implement PlaywrightRuntime singleton with startup/shutdown lifecycle",
            "Implement runtime smoke test (launch + navigate + close)",
            "Implement runtime health check with browser validation",
            "Validate browser lifecycle: launch, interact, shutdown",
            "Validate context isolation: two contexts don't share state",
            "Validate form interaction: fill, click, select, check",
            "Validate dynamic content waiting with auto-wait",
            "Validate JavaScript dialog handling via event listener",
            "Validate screenshot capture (direct + ArtifactManager)",
            "Validate built-in video recording",
            "Validate Playwright tracing (DOM snapshots + network)",
            "Validate accessibility tree access for self-healing",
            "Validate BrowserSessionManager integration",
            "Validate graceful shutdown of multiple concurrent sessions",
            "Validate metrics collection across all operations",
        ],
        files_changed=[
            FileChange(
                "backend/automation/playwright_runtime.py",
                "created",
                "PlaywrightRuntime singleton -- startup validation, smoke test, health check"
            ),
            FileChange(
                "backend/automation/playwright_driver.py",
                "modified",
                "Fixed deprecated accessibility API -- now uses aria_snapshot() with JS fallback"
            ),
            FileChange(
                "tests/fixtures/test_page.html",
                "created",
                "Integration test fixture with login form, counter, dynamic content, dialog"
            ),
            FileChange(
                "tests/test_playwright_prototype.py",
                "created",
                "16 integration tests validating entire abstraction layer end-to-end"
            ),
        ],
        risks=[
            RiskEntry(
                "R-006",
                "Playwright browser download requires internet access",
                "medium",
                "Document offline install procedure. Binaries cached in ms-playwright dir.",
                "mitigated"
            ),
            RiskEntry(
                "R-007",
                "Deprecated accessibility API in Playwright v1.41+",
                "low",
                "Replaced page.accessibility.snapshot() with aria_snapshot() + JS fallback.",
                "mitigated"
            ),
        ],
        pending_tasks=[],
        rollback_notes=(
            "Remove backend/automation/playwright_runtime.py. "
            "Revert playwright_driver.py a11y changes. "
            "Remove tests/fixtures/ and tests/test_playwright_prototype.py. "
            "Phase 2 abstraction layer remains intact."
        ),
        notes=(
            "16/16 integration tests pass in 9.72s. "
            "Chromium v147.0.7727.15 validated. "
            "Video, trace, screenshot capture all confirmed working."
        )
    ),

    PhaseEntry(
        phase_number=4,
        name="Dual Runtime Support",
        status=PhaseStatus.COMPLETED,
        started_at=datetime.utcnow().isoformat(),
        objectives=[
            "Implement dual engine subprocess executor with engine tagging",
            "Implement compatibility layer for drop-in execution replacement",
            "Wire dual engine into execution_api.py with ?engine= query param",
            "Wire dual engine into workflow.py LangGraph execute_tests node",
            "Implement automatic infrastructure-level fallback (PW -> Selenium)",
            "Add engine info diagnostic endpoint (/engine-info)",
            "Implement resolve_engine_for_project with priority chain",
            "Add is_registered_engine helper to FeatureFlags",
            "Validate timeout enforcement in dual engine subprocess",
        ],
        files_changed=[
            FileChange(
                "backend/automation/dual_engine.py",
                "created",
                "Dual engine executor with subprocess routing, fallback, and metrics"
            ),
            FileChange(
                "backend/automation/compat.py",
                "created",
                "Drop-in compatibility wrapper routing to dual engine or legacy"
            ),
            FileChange(
                "backend/automation/config.py",
                "modified",
                "Added is_registered_engine() helper to FeatureFlags"
            ),
            FileChange(
                "backend/api/execution_api.py",
                "modified",
                "Added ?engine= param, _execute_script wrapper, /engine-info endpoint"
            ),
            FileChange(
                "backend/agent/workflow.py",
                "modified",
                "Wired execute_tests node through compat layer with project_id context"
            ),
            FileChange(
                "tests/test_dual_engine.py",
                "created",
                "9 integration tests for dual engine routing and fallback"
            ),
        ],
        risks=[
            RiskEntry(
                "R-008",
                "Compat layer may shadow import errors in dual engine",
                "low",
                "Compat falls back to legacy on any ImportError with logging.",
                "mitigated"
            ),
            RiskEntry(
                "R-009",
                "Playwright script fallback to Selenium is NOT script-compatible",
                "medium",
                "Fallback only triggers on infrastructure errors, not script errors.",
                "mitigated"
            ),
        ],
        pending_tasks=[],
        rollback_notes=(
            "Remove backend/automation/dual_engine.py and compat.py. "
            "Revert execution_api.py and workflow.py changes. "
            "Revert config.py is_registered_engine addition. "
            "System reverts to direct Selenium subprocess execution."
        ),
        notes=(
            "9/9 integration tests pass in 3.33s. "
            "16/16 Phase 3 regression tests still pass. "
            "FastAPI app has 57 routes (was 56, +engine-info). "
            "Default engine is selenium with PW disabled. Zero behavior change."
        )
    ),

    PhaseEntry(
        phase_number=5,
        name="AI Script Generation Migration",
        status=PhaseStatus.IN_PROGRESS,
        started_at=datetime.utcnow().isoformat(),
        objectives=[
            "Create Playwright prompt template with sync_api instructions",
            "Implement semantic locator priority (testid > role > label > text > CSS)",
            "Instruct event-based dialog handling (page.on('dialog'))",
            "Instruct auto-waiting (no time.sleep)",
            "Maintain identical stdout metadata format for parser compatibility",
            "Create engine-aware script generation router (script_gen.py)",
            "Wire engine-aware generator into LangGraph workflow",
            "Add prompt preview endpoint (get_prompt)",
            "Validate Selenium prompt structure (regression)",
            "Validate cross-engine prompt differentiation",
        ],
        files_changed=[
            FileChange(
                "backend/services/playwright_service.py",
                "created",
                "Playwright prompt template + generate_playwright_script function"
            ),
            FileChange(
                "backend/automation/script_gen.py",
                "created",
                "Engine-aware routing: generate_script() + get_prompt() with fallback"
            ),
            FileChange(
                "backend/agent/workflow.py",
                "modified",
                "generate_scripts node uses engine-aware generation with project_id routing"
            ),
            FileChange(
                "tests/test_script_gen.py",
                "created",
                "10 tests for prompt structure, routing, locators, and cross-engine diff"
            ),
        ],
        risks=[
            RiskEntry(
                "R-010",
                "LLM may not follow Playwright prompt perfectly",
                "medium",
                "Prompt includes explicit code examples and anti-patterns. Self-healing in Phase 6 adds fallback.",
                "accepted"
            ),
        ],
        pending_tasks=[],
        rollback_notes=(
            "Remove backend/services/playwright_service.py. "
            "Remove backend/automation/script_gen.py. "
            "Revert workflow.py generate_scripts changes. "
            "Remove tests/test_script_gen.py. "
            "System reverts to Selenium-only script generation."
        ),
        notes=(
            "10/10 integration tests pass in 15.20s. "
            "9/9 Phase 4 regression tests pass. "
            "Prompt uses sync_api for subprocess compatibility. "
            "Same SCREENSHOT_PATH/BROWSER metadata format as Selenium."
        )
    ),

    PhaseEntry(phase_number=6, name="Self-Healing Migration", status=PhaseStatus.NOT_STARTED,
               objectives=["DOM analysis", "Locator recovery", "Trace-assisted debugging",
                           "Retry orchestration", "Browser-state recovery"]),

    PhaseEntry(phase_number=7, name="Async & Concurrency Refactor", status=PhaseStatus.NOT_STARTED,
               objectives=["Async execution workers", "Browser pools",
                           "Distributed execution", "Cancellation handling"]),

    PhaseEntry(phase_number=8, name="WebSocket Refactor", status=PhaseStatus.NOT_STARTED,
               objectives=["Async event streaming", "Live execution telemetry",
                           "Execution progress events", "Artifact streaming"]),

    PhaseEntry(phase_number=9, name="Artifact Pipeline Refactor", status=PhaseStatus.NOT_STARTED,
               objectives=["Screenshot pipeline", "Video pipeline", "Trace pipeline",
                           "Storage abstraction", "Artifact indexing"]),

    PhaseEntry(phase_number=10, name="Docker & Deployment Migration", status=PhaseStatus.NOT_STARTED,
               objectives=["Playwright Docker setup", "Browser containers",
                           "Kubernetes scaling", "CI/CD updates"]),

    PhaseEntry(phase_number=11, name="Validation & Rollout", status=PhaseStatus.NOT_STARTED,
               objectives=["Regression testing", "Concurrency testing",
                           "Load testing", "Canary rollout", "Selenium deprecation"]),
]


# ============================================================
# Ledger Query Functions
# ============================================================

def get_current_phase() -> PhaseEntry:
    """Get the currently in-progress phase."""
    for entry in MIGRATION_LEDGER:
        if entry.status == PhaseStatus.IN_PROGRESS:
            return entry
    # If no phase is in progress, return the last one
    return MIGRATION_LEDGER[-1]


def get_phase(phase_number: int) -> Optional[PhaseEntry]:
    """Get a specific phase by number."""
    for entry in MIGRATION_LEDGER:
        if entry.phase_number == phase_number:
            return entry
    return None


def get_completed_phases() -> List[PhaseEntry]:
    """Get all completed phases."""
    return [e for e in MIGRATION_LEDGER if e.status == PhaseStatus.COMPLETED]


def get_pending_phases() -> List[PhaseEntry]:
    """Get all not-started phases."""
    return [e for e in MIGRATION_LEDGER if e.status == PhaseStatus.NOT_STARTED]


def get_all_risks() -> List[RiskEntry]:
    """Get all risks across all phases."""
    risks: List[RiskEntry] = []
    for entry in MIGRATION_LEDGER:
        risks.extend(entry.risks)
    return risks


def get_open_risks() -> List[RiskEntry]:
    """Get all open (unmitigated) risks."""
    return [r for r in get_all_risks() if r.status == "open"]


def ledger_summary() -> Dict:
    """Get a high-level summary of migration progress."""
    total = len(MIGRATION_LEDGER)
    completed = len(get_completed_phases())
    in_progress = len([e for e in MIGRATION_LEDGER if e.status == PhaseStatus.IN_PROGRESS])
    not_started = len(get_pending_phases())

    return {
        "total_phases": total,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "progress_percent": round((completed / total) * 100, 1) if total > 0 else 0,
        "current_phase": get_current_phase().name,
        "open_risks": len(get_open_risks()),
        "total_risks": len(get_all_risks()),
    }
