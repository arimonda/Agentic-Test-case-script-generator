"""
Data models for the Self-Healing Autonomous Test Agent.

All domain objects are defined here as Pydantic models for
validation, serialization, and clean type safety throughout the codebase.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class LocatorStrategy(str, Enum):
    TEST_ID = "test_id"
    ID = "id"
    ARIA = "aria"
    CSS = "css"
    XPATH = "xpath"
    VISUAL = "visual"


class ActionType(str, Enum):
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    HOVER = "hover"
    NAVIGATE = "navigate"
    WAIT = "wait"
    ASSERT_VISIBLE = "assert_visible"
    ASSERT_TEXT = "assert_text"
    ASSERT_VALUE = "assert_value"
    SCREENSHOT = "screenshot"
    CUSTOM = "custom"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    HEALED = "healed"
    SKIPPED = "skipped"


class AIProvider(str, Enum):
    GEMINI = "GEMINI"
    CLAUDE = "CLAUDE"


# =============================================================================
# Locator Models
# =============================================================================

class Locator(BaseModel):
    """A single element locator with its strategy and confidence score."""
    strategy: LocatorStrategy
    value: str
    confidence: float = Field(ge=0.0, le=1.0, description="AI confidence 0-1")
    description: str = ""

    def to_playwright(self) -> str:
        """Return the Playwright Python code string for this locator."""
        match self.strategy:
            case LocatorStrategy.TEST_ID:
                return f'page.get_by_test_id("{self.value}")'
            case LocatorStrategy.ID:
                return f'page.locator("#{self.value}")'
            case LocatorStrategy.ARIA:
                return f'page.get_by_role("{self.value}")'
            case LocatorStrategy.CSS:
                return f'page.locator("{self.value}")'
            case LocatorStrategy.XPATH:
                return f'page.locator("{self.value}")'
            case LocatorStrategy.VISUAL:
                return f'page.get_by_text("{self.value}")'
            case _:
                return f'page.locator("{self.value}")'


class LocatorSet(BaseModel):
    """Ranked set of locators for a single UI element (primary -> tertiary)."""
    element_name: str
    element_description: str = ""
    primary: Locator
    secondary: Optional[Locator] = None
    tertiary: Optional[Locator] = None

    def ranked(self) -> list[Locator]:
        """Return locators in priority order, skipping None entries."""
        return [loc for loc in [self.primary, self.secondary, self.tertiary] if loc]


# =============================================================================
# Test Step Models
# =============================================================================

class TestStepInput(BaseModel):
    """A single step extracted from the requirement document (pre-execution)."""
    step_number: int
    intent: str = Field(description="What the user wants to do, e.g. 'Click Login'")
    action_type: ActionType = ActionType.CLICK
    input_data: Optional[str] = Field(None, description="Data to type/select")
    expected_result: str = Field(description="Success criteria")
    page_url: Optional[str] = None


class TestStepResult(BaseModel):
    """Execution result for a single test step."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    step_input: TestStepInput
    status: StepStatus = StepStatus.PENDING
    locators_used: Optional[LocatorSet] = None
    locator_used_index: int = 0
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    actual_result: str = ""
    error_message: str = ""
    healing_attempts: int = 0
    duration_ms: float = 0.0
    ai_reasoning: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


# =============================================================================
# Test Case Models
# =============================================================================

class TestCase(BaseModel):
    """A complete test case comprising multiple ordered steps."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str = ""
    preconditions: str = ""
    target_url: str
    steps: list[TestStepInput] = []
    tags: list[str] = []
    source_file: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class TestCaseResult(BaseModel):
    """Full execution result for a test case."""
    test_case: TestCase
    step_results: list[TestStepResult] = []
    overall_status: StepStatus = StepStatus.PENDING
    total_duration_ms: float = 0.0
    total_healing_attempts: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def passed_steps(self) -> int:
        return sum(1 for s in self.step_results if s.status == StepStatus.PASSED)

    @property
    def failed_steps(self) -> int:
        return sum(1 for s in self.step_results if s.status == StepStatus.FAILED)

    @property
    def healed_steps(self) -> int:
        return sum(1 for s in self.step_results if s.status == StepStatus.HEALED)


# =============================================================================
# Page State Model
# =============================================================================

class PageState(BaseModel):
    """Captured state of a web page at a point in time."""
    url: str
    title: str
    screenshot_path: str
    screenshot_base64: Optional[str] = None
    dom_html: str
    minified_html: str = ""
    visible_text: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


# =============================================================================
# AI Interaction Models
# =============================================================================

class AIRequest(BaseModel):
    """A request payload sent to an AI provider."""
    provider: AIProvider
    model: str
    prompt: str
    images: list[str] = Field(default_factory=list, description="Base64 images")
    temperature: float = 0.2
    max_tokens: int = 4096


class AIResponse(BaseModel):
    """A response received from an AI provider."""
    provider: AIProvider
    model: str
    content: str
    usage: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
    raw_response: Optional[Any] = None


# =============================================================================
# Requirement Extraction Models
# =============================================================================

class RequirementItem(BaseModel):
    """A single requirement extracted from a document."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    intent: str
    expected_result: str
    input_data: Optional[str] = None
    priority: str = "medium"
    source_location: str = ""


class ParsedRequirements(BaseModel):
    """Collection of requirements extracted from a document."""
    source_file: str
    file_type: str
    items: list[RequirementItem] = []
    raw_context: str = ""
    parsed_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# Configuration Model
# =============================================================================

class AppConfig(BaseModel):
    """Runtime configuration loaded from config.yaml + .env."""
    ai_provider: AIProvider = AIProvider.CLAUDE
    gemini_api_key: str = ""
    claude_api_key: str = ""
    openai_api_key: str = ""
    target_url: str = ""

    # Playwright
    headless: bool = False
    browser: str = "chromium"
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    navigation_timeout: int = 60000
    retries: int = 3
    slow_mo: int = 100
    screenshot_type: str = "full_page"

    # Self-healing
    self_healing_enabled: bool = True
    max_healing_retries: int = 3

    # Artifacts
    output_dir: str = "output"
    generate_script: bool = True
    generate_docx: bool = True
    generate_report: bool = True
    report_format: str = "html"

    # RAG
    rag_enabled: bool = True
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Models
    gemini_vision_model: str = "gemini-2.5-flash"
    gemini_text_model: str = "gemini-2.5-flash"
    claude_vision_model: str = "claude-sonnet-4-20250514"
    claude_text_model: str = "claude-sonnet-4-20250514"
    model_temperature: float = 0.2
    model_max_tokens: int = 4096
