# Self-Healing Autonomous Test Agent

# Architecture Document

**Version 1.0 | February 2026**
**Classification: Confidential — Internal Use Only**

> This document provides a complete, line-by-line architectural specification of the
> Self-Healing Autonomous Test Agent. Every module, class, method, field, constant,
> import, algorithm, data structure, prompt template, configuration parameter, and
> design decision in the codebase is described below. Nothing is omitted.

---

## Document Index

- [Part I — System Overview](#part-i--system-overview)
- [Part II — Entry Point & CLI Layer](#part-ii--entry-point--cli-layer)
- [Part III — Configuration Layer](#part-iii--configuration-layer)
- [Part IV — Data Model Layer](#part-iv--data-model-layer)
- [Part V — Core Engine Layer](#part-v--core-engine-layer)
- [Part VI — Generator Layer](#part-vi--generator-layer)
- [Part VII — Knowledge Layer](#part-vii--knowledge-layer)
- [Part VIII — Utility Layer](#part-viii--utility-layer)
- [Part IX — Cross-Cutting Concerns](#part-ix--cross-cutting-concerns)
- [Part X — Input & Test Data Layer](#part-x--input--test-data-layer)
- [Part XI — Dependency Map](#part-xi--dependency-map)

---

# Part I — System Overview

## 1.1 Purpose

The system is an AI-powered autonomous browser testing agent. It reads unstructured business requirement documents, opens a real browser via Playwright, uses AI computer vision to identify UI elements, executes test steps with self-healing locator fallback, and simultaneously generates three artifact types: Python automation scripts, Word test case documents, and HTML execution reports.

## 1.2 Architectural Style

**Pipeline architecture** with five sequential stages orchestrated by a central agent:

```
STAGE 1          STAGE 2          STAGE 3          STAGE 4          STAGE 5
INGEST    ───>   CAPTURE   ───>   INFER     ───>   EXECUTE   ───>   GENERATE
                                                                     (parallel)
```

Each stage is encapsulated in its own engine class, following the **Single Responsibility Principle**. The orchestrator (`AutonomousTestAgent`) coordinates stage transitions and data flow.

## 1.3 High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              main.py (CLI Layer)                             │
│  parse_args() → setup_logging() → load_config() → AutonomousTestAgent       │
│  display_banner() → display_results()                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────── ORCHESTRATOR ───────────────────────────────┐  │
│  │                     core/agent.py                                      │  │
│  │                  AutonomousTestAgent                                    │  │
│  │                                                                        │  │
│  │  run() ─────────────────────────────────────────────────────────────>  │  │
│  │    │                                                                   │  │
│  │    ├─ 1. RAGEngine.ingest_directory()        [OPTIONAL]               │  │
│  │    │                                                                   │  │
│  │    ├─ 2. RequirementParser.parse_file()      [STAGE 1: INGEST]        │  │
│  │    │     └─ AIEngine.infer_json()                                      │  │
│  │    │                                                                   │  │
│  │    ├─ 3. For each TestCase:                                            │  │
│  │    │     └─ _execute_test_case()                                       │  │
│  │    │         └─ For each TestStepInput:                                │  │
│  │    │             ├─ StateCaptureEngine.capture()  [STAGE 2: CAPTURE]   │  │
│  │    │             │    ├─ page.screenshot()                             │  │
│  │    │             │    ├─ page.content()                                │  │
│  │    │             │    ├─ minify_html()                                 │  │
│  │    │             │    ├─ extract_visible_text()                        │  │
│  │    │             │    └─ prepare_for_ai()                              │  │
│  │    │             │                                                     │  │
│  │    │             ├─ RAGEngine.get_context_for_step()                   │  │
│  │    │             │                                                     │  │
│  │    │             ├─ LocatorEngine.identify_locators()  [STAGE 3: INFER]│  │
│  │    │             │    └─ AIEngine.infer_json()                         │  │
│  │    │             │         ├─ _infer_gemini()  OR                      │  │
│  │    │             │         └─ _infer_claude()                          │  │
│  │    │             │                                                     │  │
│  │    │             ├─ ReportGenerator.log_ai_usage()                     │  │
│  │    │             │                                                     │  │
│  │    │             └─ ActionExecutor.execute_step()  [STAGE 4: EXECUTE]  │  │
│  │    │                  ├─ screenshot(before)                            │  │
│  │    │                  ├─ for locator in [primary, secondary, tertiary]:│  │
│  │    │                  │    ├─ _resolve_locator()                       │  │
│  │    │                  │    ├─ wait_for(visible)                        │  │
│  │    │                  │    └─ _perform_action()                        │  │
│  │    │                  └─ screenshot(after)                             │  │
│  │    │                                                                   │  │
│  │    └─ 4. _generate_artifacts_parallel()       [STAGE 5: GENERATE]     │  │
│  │         ├─ ThreadPoolExecutor(max_workers=3)                           │  │
│  │         ├─ ScriptGenerator.generate()     → .py                       │  │
│  │         ├─ DocxGenerator.generate()       → .docx                     │  │
│  │         └─ ReportGenerator.generate()     → .html + .json             │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────── SUPPORTING LAYERS ────────────────────────────────┐  │
│  │                                                                        │  │
│  │  models/schemas.py    ── 4 enums, 12 Pydantic models                  │  │
│  │  config/config.yaml   ── 75-line YAML configuration                    │  │
│  │  core/config_loader.py── load_config(): .env + YAML → AppConfig       │  │
│  │  utils/dom_utils.py   ── minify_html, extract_interactive_elements,   │  │
│  │                          extract_visible_text                          │  │
│  │  utils/screenshot_utils.py ── resize, encode, save                    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 1.4 Concurrency Model

| Execution Context | Technology | What Runs Here |
|---|---|---|
| **Main async event loop** | `asyncio` via `asyncio.run(main())` | Playwright browser automation, page navigation, screenshots, DOM capture, AI API calls (synchronous within the async context), action execution with self-healing |
| **Artifact thread pool** | `concurrent.futures.ThreadPoolExecutor(max_workers=3)` | `ScriptGenerator.generate()`, `DocxGenerator.generate()`, `ReportGenerator.generate()` — each submitted via `executor.submit()` with a 30-second `future.result(timeout=30)` |

The main loop is **single-threaded async**. Playwright's async API (`playwright.async_api`) is used throughout. AI inference calls (`AIEngine.infer()`) are synchronous HTTP calls that block the event loop — this is intentional since each step must complete its AI inference before action execution can proceed.

Artifact generation happens **after** all test execution completes. The three generators run in parallel on a `ThreadPoolExecutor` with 3 workers, allowing script, docx, and report to be written simultaneously.

## 1.5 Technology Stack

| Layer | Package | Version | Role in System |
|---|---|---|---|
| Runtime | Python | 3.9+ | Core language |
| Browser Automation | `playwright` | 1.49.1 | Browser launch, navigation, screenshots, DOM capture, element interaction |
| AI — Gemini | `google-generativeai` | 0.8.4 | Multimodal inference (native image + text) |
| AI — Claude | `anthropic` | 0.42.0 | Vision inference (base64 image messages) |
| Data Validation | `pydantic` | 2.10.4 | Type-safe Pydantic v2 models for all domain objects |
| Doc Reading | `python-docx` | 1.1.2 | Parse .docx requirement files + generate Word test cases |
| Doc Reading | `openpyxl` | 3.1.5 | Parse .xlsx requirement spreadsheets |
| Doc Convert | `docx2pdf` | 0.1.8 | Optional PDF conversion (available but not wired in main pipeline) |
| Vector DB | `chromadb` | 0.5.23 | Local persistent vector store for RAG knowledge base |
| Text Split | `langchain-text-splitters` | 0.3.4 | `RecursiveCharacterTextSplitter` for document chunking |
| LangChain | `langchain` | 0.3.14 | Available as dependency for future RAG enhancements |
| LangChain | `langchain-community` | 0.3.14 | Community integrations |
| Image | `Pillow` | 11.1.0 | Screenshot resize (LANCZOS), JPEG compression, RGB conversion |
| Config | `PyYAML` | 6.0.2 | Parse `config/config.yaml` |
| Config | `python-dotenv` | 1.0.1 | Load `.env` environment variables |
| Templates | `jinja2` | 3.1.5 | Available for template rendering (HTML reports use inline templates) |
| CLI Output | `rich` | 13.9.4 | Console, Panel, Table, RichHandler for formatted terminal output |
| Async File | `aiofiles` | 24.1.0 | Available for async file I/O (reserved for future use) |
| Retry | `tenacity` | 9.0.0 | Available for retry decorators (reserved for future use) |

---

# Part II — Entry Point & CLI Layer

## 2.1 File: `main.py` (240 lines)

### Imports

```
argparse, asyncio, logging, sys, pathlib.Path
rich.console.Console, rich.logging.RichHandler, rich.panel.Panel, rich.table.Table
core.agent.AutonomousTestAgent, core.config_loader.load_config
```

### Module-Level Objects

- `console = Console()` — Rich console instance for all terminal output

### Functions

#### `setup_logging(level: str = "INFO") → None`
- Calls `logging.basicConfig()` with `RichHandler(console=console, rich_tracebacks=True)`
- Format: `"%(message)s"` with `datefmt="[%X]"` (time only)
- Level resolved via `getattr(logging, level.upper(), logging.INFO)`

#### `parse_args() → argparse.Namespace`
Creates an `ArgumentParser` with `RawDescriptionHelpFormatter` and module docstring as epilog.

**Arguments defined (10 total):**

| Argument | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--requirements` | `-r` | `str` | None | One of -r/-t/--demo | Path to .docx or .xlsx |
| `--text` | `-t` | `str` | None | One of -r/-t/--demo | Inline requirement text |
| `--url` | `-u` | `str` | None | Yes | Target application URL |
| `--knowledge` | `-k` | `str` | None | No | RAG knowledge base directory |
| `--config` | `-c` | `str` | `"config/config.yaml"` | No | Config YAML path |
| `--demo` | — | `store_true` | `False` | No | Enable demo mode |
| `--intent` | — | `str` | None | If `--demo` | Step intent for demo mode |
| `--provider` | — | `choices=["GEMINI","CLAUDE"]` | None | No | Override AI provider |
| `--headless` | — | `store_true` | `False` | No | Headless browser |
| `--log-level` | — | `choices=[DEBUG,INFO,WARNING,ERROR]` | `"INFO"` | No | Log verbosity |

#### `display_banner() → None`
Prints a `rich.Panel` with:
- Title: `"[bold cyan]Self-Healing Autonomous Test Agent[/bold cyan]"`
- Subtitle: `"[dim]AI-Powered Browser Testing with Computer Vision & Self-Healing Locators[/dim]"`
- Border: `bright_blue`, padding `(1, 2)`

#### `display_results(results: list) → None`
For each `TestCaseResult` in results:
1. Creates a `rich.Table` with columns: `Step` (dim, w=6), `Intent` (w=40), `Status` (w=12), `Healed` (w=8), `Duration` (w=12)
2. For each `TestStepResult`: adds a row with status color-coded (`PASSED`=green, `FAILED`=red, `HEALED`=yellow)
3. Prints summary line: `Overall: {status} | Passed: {n} | Failed: {n} | Healed: {n} | Duration: {ms} ms`

#### `async main() → None`
The complete execution flow:

1. `args = parse_args()`
2. `setup_logging(args.log_level)`
3. `display_banner()`
4. `config = load_config(config_path=args.config)`
5. **CLI overrides applied:**
   - `if args.url:` → `config.target_url = args.url`
   - `if args.provider:` → lazy-import `AIProvider`, set `config.ai_provider = AIProvider(args.provider.upper())`
   - `if args.headless:` → `config.headless = True`
6. **Validation:**
   - No `target_url` → prints red error, `sys.exit(1)`
   - No `claude_api_key` AND no `gemini_api_key` → prints red error, `sys.exit(1)`
7. `agent = AutonomousTestAgent(config)`
8. **Branch: Demo mode** (`args.demo`):
   - Validates `args.intent` exists (else exit 1)
   - Calls `await agent.run_single_step(target_url=config.target_url, intent=args.intent)`
   - Prints: status, locator, duration, and error if any
9. **Branch: Full pipeline mode** (else):
   - Validates `args.requirements or args.text` (else exit 1)
   - Calls `await agent.run(requirement_file=args.requirements, requirement_text=args.text, target_url=config.target_url, knowledge_dir=args.knowledge)`
   - Calls `display_results(results)`
   - Prints `"[bold green]Artifacts generated in output/ directory[/bold green]"`
10. Entry guard: `if __name__ == "__main__": asyncio.run(main())`

---

# Part III — Configuration Layer

## 3.1 File: `config/config.yaml` (76 lines)

Six top-level sections with exact keys and defaults:

**Section `ai_provider`** (line 9): `"GEMINI"` — string, overridden by env `AI_PROVIDER`

**Section `api_keys`** (lines 12-14):
- `gemini: "${GEMINI_API_KEY}"` — placeholder, resolved from env
- `claude: "${CLAUDE_API_KEY}"` — placeholder, resolved from env

**Section `models`** (lines 17-27):
- `gemini.vision_model`: `"gemini-2.5-flash"`
- `gemini.text_model`: `"gemini-2.5-flash"`
- `gemini.max_tokens`: `4096`
- `gemini.temperature`: `0.2`
- `claude.vision_model`: `"claude-sonnet-4-20250514"`
- `claude.text_model`: `"claude-sonnet-4-20250514"`
- `claude.max_tokens`: `4096`
- `claude.temperature`: `0.2`

**Section `playwright`** (lines 30-40):
- `headless`: `false`
- `browser`: `"chromium"` (also supports `firefox`, `webkit`)
- `screenshot_type`: `"full_page"` (also supports `viewport`)
- `viewport.width`: `1920`
- `viewport.height`: `1080`
- `timeout`: `30000` (ms)
- `navigation_timeout`: `60000` (ms)
- `retries`: `3`
- `slow_mo`: `100` (ms)

**Section `self_healing`** (lines 43-52):
- `enabled`: `true`
- `max_retries`: `3`
- `locator_strategies`: ordered list — `["test_id", "id", "aria", "css", "xpath", "visual"]`

**Section `artifacts`** (lines 55-61):
- `output_dir`: `"output"`
- `generate_script`: `true`
- `generate_docx`: `true`
- `generate_report`: `true`
- `screenshot_in_docx`: `true`
- `report_format`: `"html"` (also supports `json`)

**Section `rag`** (lines 64-69):
- `enabled`: `true`
- `chunk_size`: `1000`
- `chunk_overlap`: `200`
- `embedding_model`: `"text-embedding-3-small"` (informational, ChromaDB uses built-in)
- `vector_store`: `"local"` (ChromaDB)

**Section `logging`** (lines 72-75):
- `level`: `"INFO"`
- `file`: `"output/agent.log"`
- `console`: `true`

## 3.2 File: `core/config_loader.py` (102 lines)

### Imports
`logging, os, pathlib.Path, yaml, dotenv.load_dotenv, models.schemas.AIProvider, models.schemas.AppConfig`

### Function: `load_config(config_path="config/config.yaml", env_path=".env") → AppConfig`

**Step 1:** Load `.env` — if file exists, calls `load_dotenv(env_file)` which injects key-value pairs into `os.environ`.

**Step 2:** Load YAML — if file exists, `yaml.safe_load()`. If not found, uses empty dict `{}` and logs a warning.

**Step 3:** Extract nested YAML sections into local variables:
```python
pw = yaml_config.get("playwright", {})
models = yaml_config.get("models", {})
healing = yaml_config.get("self_healing", {})
artifacts = yaml_config.get("artifacts", {})
rag = yaml_config.get("rag", {})
viewport = pw.get("viewport", {})
gemini_models = models.get("gemini", {})
claude_models = models.get("claude", {})
```

**Step 4:** Construct `AppConfig` with **33 fields**, each resolved as:
- Environment variable (via `os.getenv()`) for: `AI_PROVIDER`, `GEMINI_API_KEY`, `CLAUDE_API_KEY`, `OPENAI_API_KEY`, `TARGET_URL`
- YAML value (via `.get()`) for all other settings
- Built-in default as final fallback

**Returns** validated `AppConfig` Pydantic model. Logs provider and URL.

---

# Part IV — Data Model Layer

## 4.1 File: `models/schemas.py` (285 lines)

### Imports
`__future__.annotations, uuid, datetime, enum.Enum, pathlib.Path, typing.Any, typing.Optional, pydantic.BaseModel, pydantic.Field`

### 4 Enumerations

#### `LocatorStrategy(str, Enum)` — 6 values
| Value | String | Playwright Mapping |
|---|---|---|
| `TEST_ID` | `"test_id"` | `page.get_by_test_id(value)` |
| `ID` | `"id"` | `page.locator(f"#{value}")` |
| `ARIA` | `"aria"` | `page.get_by_role(role, name=name)` if `=` in value, else `page.get_by_label(value)` |
| `CSS` | `"css"` | `page.locator(value)` |
| `XPATH` | `"xpath"` | `page.locator(value)` |
| `VISUAL` | `"visual"` | `page.get_by_text(value)` |

#### `ActionType(str, Enum)` — 13 values
`click, fill, select, check, uncheck, hover, navigate, wait, assert_visible, assert_text, assert_value, screenshot, custom`

#### `StepStatus(str, Enum)` — 6 values
`pending, running, passed, failed, healed, skipped`

#### `AIProvider(str, Enum)` — 2 values
`GEMINI, CLAUDE`

### 12 Pydantic Models

#### `Locator(BaseModel)`
| Field | Type | Default | Constraint | Description |
|---|---|---|---|---|
| `strategy` | `LocatorStrategy` | required | — | How to find the element |
| `value` | `str` | required | — | The selector string |
| `confidence` | `float` | required | `ge=0.0, le=1.0` | AI confidence score |
| `description` | `str` | `""` | — | Why this locator was chosen |

**Method `to_playwright() → str`:** Uses `match self.strategy` with 7 cases (6 strategies + `_` wildcard) to return the Playwright Python code string. Each case returns an f-string like `'page.get_by_test_id("{self.value}")'`.

#### `LocatorSet(BaseModel)`
| Field | Type | Default |
|---|---|---|
| `element_name` | `str` | required |
| `element_description` | `str` | `""` |
| `primary` | `Locator` | required |
| `secondary` | `Optional[Locator]` | `None` |
| `tertiary` | `Optional[Locator]` | `None` |

**Method `ranked() → list[Locator]`:** Returns `[loc for loc in [self.primary, self.secondary, self.tertiary] if loc]` — filters out `None` entries, preserving priority order.

#### `TestStepInput(BaseModel)`
| Field | Type | Default | Description |
|---|---|---|---|
| `step_number` | `int` | required | Sequential index |
| `intent` | `str` | required | `Field(description="What the user wants to do")` |
| `action_type` | `ActionType` | `ActionType.CLICK` | Browser action to perform |
| `input_data` | `Optional[str]` | `None` | `Field(description="Data to type/select")` |
| `expected_result` | `str` | required | `Field(description="Success criteria")` |
| `page_url` | `Optional[str]` | `None` | URL for navigate actions |

#### `TestStepResult(BaseModel)`
| Field | Type | Default |
|---|---|---|
| `step_id` | `str` | `Field(default_factory=lambda: str(uuid.uuid4())[:8])` |
| `step_input` | `TestStepInput` | required |
| `status` | `StepStatus` | `StepStatus.PENDING` |
| `locators_used` | `Optional[LocatorSet]` | `None` |
| `locator_used_index` | `int` | `0` |
| `screenshot_before` | `Optional[str]` | `None` |
| `screenshot_after` | `Optional[str]` | `None` |
| `actual_result` | `str` | `""` |
| `error_message` | `str` | `""` |
| `healing_attempts` | `int` | `0` |
| `duration_ms` | `float` | `0.0` |
| `ai_reasoning` | `str` | `""` |
| `timestamp` | `datetime` | `Field(default_factory=datetime.now)` |

#### `TestCase(BaseModel)`
| Field | Type | Default |
|---|---|---|
| `id` | `str` | `Field(default_factory=lambda: str(uuid.uuid4())[:8])` |
| `name` | `str` | required |
| `description` | `str` | `""` |
| `preconditions` | `str` | `""` |
| `target_url` | `str` | required |
| `steps` | `list[TestStepInput]` | `[]` |
| `tags` | `list[str]` | `[]` |
| `source_file` | `Optional[str]` | `None` |
| `created_at` | `datetime` | `Field(default_factory=datetime.now)` |

#### `TestCaseResult(BaseModel)`
| Field | Type | Default |
|---|---|---|
| `test_case` | `TestCase` | required |
| `step_results` | `list[TestStepResult]` | `[]` |
| `overall_status` | `StepStatus` | `StepStatus.PENDING` |
| `total_duration_ms` | `float` | `0.0` |
| `total_healing_attempts` | `int` | `0` |
| `started_at` | `Optional[datetime]` | `None` |
| `completed_at` | `Optional[datetime]` | `None` |

**Computed properties:**
- `passed_steps → int`: `sum(1 for s in self.step_results if s.status == StepStatus.PASSED)`
- `failed_steps → int`: `sum(1 for s in self.step_results if s.status == StepStatus.FAILED)`
- `healed_steps → int`: `sum(1 for s in self.step_results if s.status == StepStatus.HEALED)`

#### `PageState(BaseModel)`
| Field | Type | Default |
|---|---|---|
| `url` | `str` | required |
| `title` | `str` | required |
| `screenshot_path` | `str` | required |
| `screenshot_base64` | `Optional[str]` | `None` |
| `dom_html` | `str` | required |
| `minified_html` | `str` | `""` |
| `visible_text` | `str` | `""` |
| `timestamp` | `datetime` | `Field(default_factory=datetime.now)` |

#### `AIRequest(BaseModel)`
| Field | Type | Default |
|---|---|---|
| `provider` | `AIProvider` | required |
| `model` | `str` | required |
| `prompt` | `str` | required |
| `images` | `list[str]` | `Field(default_factory=list)` |
| `temperature` | `float` | `0.2` |
| `max_tokens` | `int` | `4096` |

#### `AIResponse(BaseModel)`
| Field | Type | Default |
|---|---|---|
| `provider` | `AIProvider` | required |
| `model` | `str` | required |
| `content` | `str` | required |
| `usage` | `dict[str, Any]` | `Field(default_factory=dict)` |
| `latency_ms` | `float` | `0.0` |
| `raw_response` | `Optional[Any]` | `None` |

#### `RequirementItem(BaseModel)`
| Field | Type | Default |
|---|---|---|
| `id` | `str` | `Field(default_factory=lambda: str(uuid.uuid4())[:8])` |
| `intent` | `str` | required |
| `expected_result` | `str` | required |
| `input_data` | `Optional[str]` | `None` |
| `priority` | `str` | `"medium"` |
| `source_location` | `str` | `""` |

#### `ParsedRequirements(BaseModel)`
| Field | Type | Default |
|---|---|---|
| `source_file` | `str` | required |
| `file_type` | `str` | required |
| `items` | `list[RequirementItem]` | `[]` |
| `raw_context` | `str` | `""` |
| `parsed_at` | `datetime` | `Field(default_factory=datetime.now)` |

#### `AppConfig(BaseModel)` — 33 fields
Groups: AI keys (5), Playwright (9), Self-healing (2), Artifacts (5), RAG (3), Models (6), Temperature/tokens (2). See Part III Section 3.2 for the full field list with types and defaults.

---

# Part V — Core Engine Layer

## 5.1 File: `core/agent.py` — AutonomousTestAgent (339 lines)

### Imports
`asyncio, logging, time, concurrent.futures.ThreadPoolExecutor, datetime, pathlib.Path, typing.Optional, playwright.async_api.{async_playwright, Browser, BrowserContext, Page}`, plus all core engines, generators, RAGEngine, and schema models.

### Class: `AutonomousTestAgent`

**`__init__(self, config: AppConfig)`** — Instantiates all sub-engines:
- `self.ai_engine = AIEngine(config)`
- `self.locator_engine = LocatorEngine(self.ai_engine)`
- `self.state_capture = StateCaptureEngine(output_dir=f"{config.output_dir}/screenshots")`
- `self.action_executor = ActionExecutor(max_retries=config.max_healing_retries, action_timeout=config.timeout, output_dir=f"{config.output_dir}/screenshots")`
- `self.requirement_parser = RequirementParser(self.ai_engine)`
- `self.rag_engine = RAGEngine(...) if config.rag_enabled else None` — with `persist_dir`, `chunk_size`, `chunk_overlap` from config
- `self.script_gen = ScriptGenerator(f"{config.output_dir}/scripts")`
- `self.docx_gen = DocxGenerator(f"{config.output_dir}/testcases")`
- `self.report_gen = ReportGenerator(f"{config.output_dir}/reports")`
- `self._executor = ThreadPoolExecutor(max_workers=3)`

**`async run(requirement_file, requirement_text, target_url, knowledge_dir) → list[TestCaseResult]`**

Complete pipeline — see Part I diagram. Key implementation details:
- Browser launched with `pw.chromium.launch(headless=config.headless, slow_mo=config.slow_mo)`
- Context created with `viewport={"width": config.viewport_width, "height": config.viewport_height}`
- All test cases executed sequentially within the same browser context
- Browser and context closed before artifact generation
- Results logged with pass/fail/heal counts per test case

**`async run_single_step(target_url, intent, action_type="click", input_data=None) → TestStepResult`**

Demo mode flow:
1. Creates `TestStepInput(step_number=1, intent=intent, action_type=ActionType(action_type), input_data=input_data, expected_result="Step completes successfully")`
2. Launches standalone browser + context + page
3. Navigates with `wait_until="networkidle"`
4. Captures state, identifies locators, executes step
5. Closes everything and returns result

**`_parse_requirements(file_path, raw_text, target_url) → list[TestCase]`** — Delegates to `requirement_parser.parse_file()` or `.parse_text()`. Raises `ValueError` if neither provided.

**`async _execute_test_case(context, test_case) → TestCaseResult`**

Per-step loop:
1. Opens new page: `context.new_page()`
2. Navigates to `test_case.target_url` with `wait_until="networkidle"` and `timeout=config.navigation_timeout`
3. Starts `time.perf_counter()` timer
4. For each step: capture → RAG context → locator identification → log AI usage → execute with self-healing → append result → accumulate healing attempts
5. On step failure: logs warning but **continues** with remaining steps (does not abort)
6. Overall status logic: `FAILED if any failed, HEALED if any healed, else PASSED`
7. Closes page

**`_generate_artifacts_parallel(results) → None`**

For each `TestCaseResult`:
- If `config.generate_script`: submits `script_gen.generate(result)` to thread pool
- If `config.generate_docx`: submits `docx_gen.generate(result)` to thread pool
- If `config.generate_report`: submits `report_gen.generate(result)` to thread pool
- Waits for all futures with `timeout=30`, logs path or error for each

## 5.2 File: `core/ai_engine.py` — AIEngine (228 lines)

### Imports
`json, logging, time, typing.Optional, anthropic, google.generativeai as genai, models.schemas.{AIProvider, AIRequest, AIResponse, AppConfig}`

### Class: `AIEngine`

**`__init__(self, config: AppConfig)`** — Stores config, calls `_init_providers()`.

**`_init_providers()`:**
- If `config.gemini_api_key`: `genai.configure(api_key=config.gemini_api_key)`
- If `config.claude_api_key`: `self._claude_client = anthropic.Anthropic(api_key=config.claude_api_key)`
- Else: `self._claude_client = None`

**`infer(prompt, images=None, provider=None, temperature=None, max_tokens=None) → AIResponse`:**
1. Resolves `active_provider` (param > config default), `temp` (param > config), `tokens` (param > config)
2. Constructs `AIRequest` with model from `_get_model_name(active_provider, has_images=bool(imgs))`
3. Logs: provider, model, image count, prompt length
4. Starts `time.perf_counter()`
5. Dispatches: `GEMINI → _infer_gemini()`, `CLAUDE → _infer_claude()`, else `ValueError`
6. Records `response.latency_ms`
7. Logs: response length, latency, usage dict

**`_infer_gemini(request) → AIResponse`:**
1. Imports `base64` locally
2. Creates `genai.GenerativeModel(request.model)`
3. Builds `parts` list: for each base64 image → `{"mime_type": "image/jpeg", "data": base64.b64decode(img_b64)}`, then appends `request.prompt` as text
4. Creates `genai.types.GenerationConfig(temperature=request.temperature, max_output_tokens=request.max_tokens)`
5. Calls `model.generate_content(parts, generation_config=generation_config)`
6. Extracts usage: checks `hasattr(response, "usage_metadata")`, uses `getattr()` with 0 defaults for `prompt_token_count`, `candidates_token_count`, `total_token_count`
7. Returns `AIResponse(provider=GEMINI, model, content=response.text, usage)`

**`_infer_claude(request) → AIResponse`:**
1. Validates `self._claude_client` exists (else `RuntimeError`)
2. Builds `content_blocks`: for each base64 image → `{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}}`, then `{"type": "text", "text": request.prompt}`
3. Calls `self._claude_client.messages.create(model, max_tokens, temperature, messages=[{"role": "user", "content": content_blocks}])`
4. Extracts usage: `response.usage.input_tokens`, `response.usage.output_tokens`
5. Returns `AIResponse(provider=CLAUDE, model, content=response.content[0].text, usage, raw_response=response)`

**`_get_model_name(provider, has_images) → str`:** Returns vision model if images present, text model otherwise. Raises `ValueError` for unknown provider.

**`infer_json(prompt, images=None, provider=None) → dict`:**
1. Calls `self.infer(prompt, images, provider)`
2. Strips response: if starts with `"```"`, removes all lines starting with `` ``` ``
3. Calls `json.loads(text)` and returns the dict

## 5.3 File: `core/locator_engine.py` — LocatorEngine (164 lines)

### Constant: `LOCATOR_PROMPT_TEMPLATE` (73 lines)

Full prompt text with placeholders: `{intent}`, `{action_type}`, `{input_data}`, `{url}`, `{title}`, `{html_snippet}`

**Prompt structure:**
1. Role: "You are an expert Playwright test automation engineer."
2. Task: "Analyze the provided screenshot and HTML to identify the UI element described below."
3. Target Element: intent, action, input data
4. Page Context: URL, title
5. HTML: minified snippet in a code block
6. Instructions: 3-step process (study screenshot, cross-reference HTML, return JSON)
7. JSON schema: exact format with `element_name`, `element_description`, `primary`, `secondary`, `tertiary` — each with `strategy`, `value`, `confidence`, `description`
8. Priority rule: "Prioritize: data-testid > id > aria-label > CSS > XPath > visual text."

### Class: `LocatorEngine`

**`__init__(self, ai_engine: AIEngine)`** — Stores reference.

**`identify_locators(page_state, step, provider=None) → LocatorSet`:**
1. Formats `LOCATOR_PROMPT_TEMPLATE` with step and page state data. HTML snippet truncated to first 15,000 chars: `page_state.minified_html[:15000]`
2. Attaches `page_state.screenshot_base64` as image (if present)
3. Calls `self.ai.infer_json(prompt, images=images, provider=provider)`
4. On success: `_parse_locator_response(data)`
5. On `json.JSONDecodeError`: logs error, returns `_fallback_locator(step)`
6. On any other `Exception`: logs error, returns `_fallback_locator(step)`

**`identify_multiple_locators(page_state, steps) → list[LocatorSet]`:** Sequential loop calling `identify_locators` for each step.

**`_parse_locator_response(data: dict) → LocatorSet`:**
- Inner function `_parse_locator(loc_data)`: creates `Locator(strategy=LocatorStrategy(loc_data["strategy"]), value=loc_data["value"], confidence=float(loc_data.get("confidence", 0.5)), description=loc_data.get("description", ""))`
- Parses `primary` (always), `secondary` (if present), `tertiary` (if present)
- Returns `LocatorSet` with `element_name` and `element_description` from data

**`_fallback_locator(step) → LocatorSet`:** Returns `LocatorSet` with a single visual locator: `Locator(strategy=VISUAL, value=step.intent, confidence=0.3, description="Fallback text-based locator")`

## 5.4 File: `core/action_executor.py` — ActionExecutor (233 lines)

### Imports
`logging, time, typing.Optional, playwright.async_api.{Page, TimeoutError as PlaywrightTimeout}, models.schemas.{ActionType, Locator, LocatorSet, StepStatus, TestStepInput, TestStepResult}, utils.screenshot_utils.save_screenshot`

### Class: `ActionExecutor`

**`__init__(self, max_retries=3, action_timeout=10000, output_dir="output/screenshots")`**

**`async execute_step(page, step, locators) → TestStepResult`:**

Complete self-healing algorithm:
1. Create `TestStepResult(step_input=step, locators_used=locators)`
2. Start `time.perf_counter()`
3. **Before screenshot:** `await page.screenshot(full_page=False)` → `save_screenshot()` → stores path in `result.screenshot_before`. Wrapped in try/except.
4. **Self-healing loop:**
   ```
   ranked = locators.ranked()   # [primary, secondary?, tertiary?]
   last_error = None
   for idx, locator in enumerate(ranked):
       try:
           log "Trying {strategy} locator ({value})"
           await self._perform_action(page, step, locator)
           result.locator_used_index = idx
           result.status = HEALED if idx > 0 else PASSED
           result.healing_attempts = idx
           result.actual_result = f"Action succeeded using {strategy} locator"
           if idx > 0: log "HEALED: Primary failed, succeeded with {strategy}"
           else: log "PASSED with primary locator"
           break
       except (PlaywrightTimeout, Exception) as exc:
           last_error = str(exc)
           log warning
           result.healing_attempts = idx + 1
           continue
   else:  # Python for/else — executed when loop completes without break
       result.status = FAILED
       result.error_message = f"All {n} locators failed. Last error: {last_error}"
       log error
   ```
5. **After screenshot:** same as before, stores in `result.screenshot_after`
6. Records `result.duration_ms`
7. Returns result

**`async _perform_action(page, step, locator) → None`:**
1. `pw_locator = self._resolve_locator(page, locator)`
2. `await pw_locator.wait_for(state="visible", timeout=self.action_timeout)`
3. `match step.action_type:` — **13 cases:**

| Case | Playwright Call |
|---|---|
| `CLICK` | `await pw_locator.click(timeout=self.action_timeout)` |
| `FILL` | `await pw_locator.fill(step.input_data or "", timeout=self.action_timeout)` |
| `SELECT` | `await pw_locator.select_option(step.input_data or "", timeout=self.action_timeout)` |
| `CHECK` | `await pw_locator.check(timeout=self.action_timeout)` |
| `UNCHECK` | `await pw_locator.uncheck(timeout=self.action_timeout)` |
| `HOVER` | `await pw_locator.hover(timeout=self.action_timeout)` |
| `NAVIGATE` | `url = step.input_data or step.page_url or ""; await page.goto(url, wait_until="networkidle")` |
| `WAIT` | `await page.wait_for_timeout(int(step.input_data or "2000"))` |
| `ASSERT_VISIBLE` | `await pw_locator.wait_for(state="visible", timeout=self.action_timeout)` |
| `ASSERT_TEXT` | `actual = await pw_locator.text_content(); if expected.lower() not in (actual or "").lower(): raise AssertionError` |
| `ASSERT_VALUE` | `actual = await pw_locator.input_value(); if expected != actual: raise AssertionError` |
| `SCREENSHOT` | `pass` (captured automatically) |
| `_` (wildcard) | `logger.warning("Unknown action type")` |

**`_resolve_locator(page, locator) → Playwright Locator`:**

| Strategy | Resolution |
|---|---|
| `TEST_ID` | `page.get_by_test_id(locator.value)` |
| `ID` | `page.locator(f"#{locator.value}")` |
| `ARIA` | If `"="` in value: `role, name = value.split("=", 1); page.get_by_role(role.strip(), name=name.strip())`. Else: `page.get_by_label(locator.value)` |
| `CSS` | `page.locator(locator.value)` |
| `XPATH` | `page.locator(locator.value)` |
| `VISUAL` | `page.get_by_text(locator.value)` |
| `_` | `page.locator(locator.value)` |

## 5.5 File: `core/state_capture.py` — StateCaptureEngine (93 lines)

### Imports
`logging, datetime, pathlib.Path, playwright.async_api.Page, models.schemas.PageState, utils.dom_utils.{extract_visible_text, minify_html}, utils.screenshot_utils.{prepare_for_ai, save_screenshot}`

**`__init__(self, output_dir="output/screenshots")`** — Creates directory with `Path(output_dir).mkdir(parents=True, exist_ok=True)`.

**`async capture(page, step_label="page", full_page=True) → PageState`:**
1. Log URL and label
2. `await page.wait_for_load_state("networkidle", timeout=10000)` — wrapped in try/except, warns on timeout
3. Generate filename: `f"{step_label}_{datetime.now():%Y%m%d_%H%M%S}.png"`
4. `screenshot_bytes = await page.screenshot(full_page=full_page)`
5. `screenshot_path = save_screenshot(screenshot_bytes, self.output_dir, filename)`
6. `screenshot_b64 = prepare_for_ai(screenshot_bytes)` — resize to 1280x1024 max, JPEG, base64
7. `dom_html = await page.content()`
8. `minified = minify_html(dom_html)`
9. `visible_text = extract_visible_text(dom_html)`
10. Assemble `PageState(url=page.url, title=await page.title(), screenshot_path, screenshot_base64, dom_html, minified_html, visible_text)`
11. Log sizes: screenshot path, DOM chars, minified chars

**`async capture_element(page, selector, label="element") → bytes | None`:**
1. `element = page.locator(selector)`
2. If `await element.count() > 0`: returns `await element.first.screenshot()`
3. On exception: warns and returns `None`

## 5.6 File: `core/requirement_parser.py` — RequirementParser (215 lines)

### Constant: `PARSE_PROMPT_TEMPLATE` (30 lines)

Prompt with placeholder `{requirement_text}`. Instructs AI to return JSON with `test_case_name`, `description`, `preconditions`, and `steps[]` array. Each step has `step_number`, `intent`, `action_type` (13 valid values listed), `input_data`, `expected_result`. Rules: atomic steps, navigate first if URL mentioned, include assertions, use "fill" for text entry.

### Class: `RequirementParser`

**`__init__(self, ai_engine: AIEngine)`**

**`parse_file(file_path, target_url="") → list[TestCase]`:**
1. Validates path exists (else `FileNotFoundError`)
2. Routes by extension: `.docx` → `_extract_docx()`, `.xlsx` → `_extract_xlsx()`, else `ValueError`
3. Calls `_ai_parse(raw_text, target_url, str(path))`

**`parse_text(text, target_url="") → list[TestCase]`:** Direct pass-through to `_ai_parse(text, target_url, "direct_input")`.

**`_extract_docx(path) → str`:**
1. Opens with `DocxDocument(str(path))`
2. Collects `para.text.strip()` for all non-empty paragraphs
3. Collects table cells: for each table, each row, joins non-empty `cell.text.strip()` with ` | `
4. Returns `"\n".join(paragraphs)`

**`_extract_xlsx(path) → str`:**
1. Opens with `openpyxl.load_workbook(str(path), data_only=True)`
2. For each sheet: adds `"=== Sheet: {name} ==="`
3. Row 1 = headers (joined with ` | `)
4. Subsequent rows: `"{header}: {value}; {header}: {value}; ..."` for non-empty cells
5. Returns `"\n".join(lines)`

**`_ai_parse(raw_text, target_url, source) → list[TestCase]`:**
1. Chunks text via `_chunk_text(raw_text, max_chars=8000)`
2. For each chunk:
   - Formats `PARSE_PROMPT_TEMPLATE` with chunk
   - Calls `self.ai.infer_json(prompt)` — wrapped in try/except, continues on failure
   - Iterates `data.get("steps", [])`: converts `action_type` string to `ActionType` enum (defaults to `CLICK` on `ValueError`), creates `TestStepInput`
   - Assembles `TestCase` with name, description, preconditions, target_url, steps, source_file

**`_chunk_text(text, max_chars=8000) → list[str]`:**
- If text fits: returns `[text]`
- Otherwise: splits by `"\n"`, accumulates lines into chunks, starts new chunk when `current_len + len(line) + 1 > max_chars`

---

# Part VI — Generator Layer

## 6.1 File: `generators/script_generator.py` — ScriptGenerator (191 lines)

### Imports
`logging, datetime, pathlib.Path, textwrap.{dedent, indent}, models.schemas.{ActionType, LocatorSet, StepStatus, TestCase, TestCaseResult, TestStepResult}`

**`generate(test_result) → str`:** Calls `_build_script()`, writes to `test_{safe_name}.py`.

**`_build_script(test_result) → str`:** Assembles 4 sections:
1. **Header** (via `dedent`): docstring with test case name, description, URL, timestamp, source; imports `re`, `playwright.sync_api.{Playwright, sync_playwright, expect}`
2. **Setup** (via `dedent`): `def run(playwright: Playwright)` with `chromium.launch(headless=False)`, `new_context(viewport)`, `new_page()`, `goto(url)`, `wait_for_load_state("networkidle")`
3. **Steps**: via `_build_steps()` — generates per-step code with comments
4. **Teardown** (via `dedent`): `context.close()`, `browser.close()`, `with sync_playwright()` wrapper

**`_build_steps(test_result) → str`:** For each step result:
- Comment lines: `# Step N: intent`, `# Expected: result`, `# Element: name`
- Active code: `_build_action_code(step, locators)` — 13-case match statement generating Playwright calls
- Backup comments: `# Backup N (strategy): locator_code` for secondary/tertiary
- Healing note: if status == HEALED, adds `# NOTE: Self-healed`
- Warning: if no locators, adds `# TODO: Manually add locator`

**`_build_action_code(step, locators) → str`:** Match on `step.action_type`:
- `CLICK`: `{loc}.click()`
- `FILL`: `{loc}.fill("{data}")`
- `SELECT`: `{loc}.select_option("{data}")`
- `CHECK/UNCHECK`: `{loc}.check()` / `{loc}.uncheck()`
- `HOVER`: `{loc}.hover()`
- `NAVIGATE`: `page.goto("{url}")`
- `WAIT`: `page.wait_for_timeout({ms})`
- `ASSERT_VISIBLE`: `expect({loc}).to_be_visible()`
- `ASSERT_TEXT`: `expect({loc}).to_contain_text("{result}")`
- `ASSERT_VALUE`: `expect({loc}).to_have_value("{result}")`
- `SCREENSHOT`: `page.screenshot(path="step_N.png")`
- Default: `# TODO: Implement action`

**`_safe_name(name) → str`:** Regex replaces non-alphanumeric to `_`, collapses multiple `_`, strips, truncates to 60 chars.

## 6.2 File: `generators/docx_generator.py` — DocxGenerator (213 lines)

### Imports
`logging, datetime, pathlib.Path, typing.Optional, docx.Document, docx.enum.table.WD_TABLE_ALIGNMENT, docx.enum.text.WD_ALIGN_PARAGRAPH, docx.shared.{Cm, Inches, Pt, RGBColor}, models.schemas.{StepStatus, TestCaseResult}`

**`generate(test_result) → str`:** Creates `Document()`, calls 4 private methods, saves to `TC_{name}_{timestamp}.docx`.

**`_add_title(doc, title)`:** Heading level 0 (centered), subtitle paragraph (centered) with gray `Pt(10)` text showing generator name and timestamp.

**`_add_metadata(doc, result)`:** Heading "Test Case Information", 2-column table with `"Light Grid Accent 1"` style. 7 metadata rows: Test Case ID, Description, Preconditions, Target URL, Source File, Total Steps, Overall Status. Labels bold.

**`_add_steps_table(doc, result)`:** Heading "Test Steps", 6-column table (centered, `"Light Grid Accent 1"` style). Header row: Step #, Action, Input Data, Expected Result, Status, Locator — all bold centered `Pt(9)`. Data rows: step data with locator primary value or "N/A". Status cell **color-coded** via `_status_color()`. All cell fonts set to `Pt(9)`. Calls `_add_screenshots_section()` after table.

**`_add_screenshots_section(doc, result)`:** Heading "Execution Screenshots". For each step: H2 heading, "Before:" paragraph + `doc.add_picture(path, width=Inches(5.5))`, "After:" paragraph + picture. Error messages in red `RGBColor(200, 0, 0)` at `Pt(9)`.

**`_add_summary(doc, result)`:** Heading "Execution Summary". 7 bullet items: Total Steps, Passed, Failed, Self-Healed, Total Duration (ms), Total Healing Attempts, Overall Status.

**`_status_color(status) → RGBColor`:**
- PASSED: `RGBColor(0, 150, 0)` — green
- FAILED: `RGBColor(200, 0, 0)` — red
- HEALED: `RGBColor(200, 150, 0)` — amber
- RUNNING: `RGBColor(0, 100, 200)` — blue
- PENDING: `RGBColor(128, 128, 128)` — gray
- SKIPPED: `RGBColor(128, 128, 128)` — gray
- Default: `RGBColor(0, 0, 0)` — black

## 6.3 File: `generators/report_generator.py` — ReportGenerator (350 lines)

### Constants

**`HTML_TEMPLATE`** (202 lines): Complete HTML5 document with embedded CSS. Dark theme using CSS custom properties:
- `--bg: #0f172a`, `--surface: #1e293b`, `--border: #334155`
- `--text: #e2e8f0`, `--text-muted: #94a3b8`
- `--green: #22c55e`, `--red: #ef4444`, `--yellow: #eab308`, `--blue: #3b82f6`

Layout: `.container` (1200px max), `.stats-grid` (CSS Grid, auto-fit, minmax(180px, 1fr)), `.stat-card` (12px rounded, centered), `.step-card` (12px rounded, 1.5rem padding), `.badge` (pill shape, 9999px radius), `.locator-info` (monospace font), `.ai-section` (table with border-bottom), `.screenshots` (flex with gap).

Template placeholders: `{test_name}`, `{description}`, `{timestamp}`, `{total_steps}`, `{passed}`, `{failed}`, `{healed}`, `{duration}`, `{total_tokens}`, `{step_cards}`, `{ai_log_rows}`.

**`STEP_CARD_TEMPLATE`** (17 lines): Card HTML with `{step_number}`, `{intent}`, `{status_class}`, `{status}`, `{action_type}`, `{input_data}`, `{expected}`, `{actual}`, `{duration_ms}`, `{locator_html}`, `{error_html}`.

### Class: `ReportGenerator`

**`__init__(self, output_dir="output/reports")`** — Creates dir, initializes `self._ai_log: list[dict[str, Any]] = []`.

**`log_ai_usage(step_number, provider, tokens, latency_ms, reasoning)`:** Appends dict with `reasoning[:200]` truncated.

**`generate(test_result) → str`:**
1. Builds step cards: for each `TestStepResult`, formats `STEP_CARD_TEMPLATE` with status class, locator info (if present: `primary.to_playwright()` with confidence percentage), error HTML
2. Builds AI log rows: iterates `self._ai_log`, sums `total_tokens`, formats HTML `<tr>` rows
3. Formats `HTML_TEMPLATE` with all placeholders
4. Saves to `report_{name}_{timestamp}.html`
5. Calls `_save_json_report()` with `.json` suffix
6. Returns HTML file path

**`_save_json_report(test_result, filepath)`:** Builds dict with:
- `"test_case"`: `test_result.test_case.model_dump(mode="json")`
- `"step_results"`: list of `sr.model_dump(mode="json")`
- `"summary"`: `overall_status`, `passed`, `failed`, `healed`, `total_duration_ms`, `total_healing_attempts`
- `"ai_usage"`: `self._ai_log`
- Writes with `json.dumps(data, indent=2, default=str)`

---

# Part VII — Knowledge Layer

## 7.1 File: `knowledge/rag_engine.py` — RAGEngine (171 lines)

### Imports
`logging, pathlib.Path, typing.Optional, docx.Document as DocxDocument, langchain_text_splitters.RecursiveCharacterTextSplitter`

### Class: `RAGEngine`

**`__init__(self, persist_dir, chunk_size=1000, chunk_overlap=200, collection_name="knowledge_base")`:**
- Stores all params
- `self._client = None` (lazy init)
- `self._collection = None`
- `self._splitter = RecursiveCharacterTextSplitter(chunk_size, chunk_overlap, separators=["\n\n", "\n", ". ", " ", ""])`

**`_ensure_initialized()`:**
- Lazy import: `import chromadb`
- Creates directory: `Path(self.persist_dir).mkdir(parents=True, exist_ok=True)`
- `self._client = chromadb.PersistentClient(path=self.persist_dir)`
- `self._collection = self._client.get_or_create_collection(name=self.collection_name, metadata={"hnsw:space": "cosine"})`
- Logs collection count

**`ingest_document(file_path) → int`:**
1. Calls `_ensure_initialized()`
2. Routes: `.docx` → `_read_docx()`, `.txt`/`.md` → `path.read_text(encoding="utf-8")`, else `ValueError`
3. `chunks = self._splitter.split_text(text)`
4. If empty: warns, returns 0
5. Generates IDs: `f"{path.stem}_chunk_{i}"`
6. Generates metadatas: `{"source": str(path), "chunk_index": i}`
7. `self._collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)` — idempotent
8. Returns chunk count

**`ingest_directory(dir_path) → int`:** Globs `*.docx`, `*.txt`, `*.md`, calls `ingest_document` for each, returns total.

**`query(question, n_results=5) → list[dict]`:**
1. `_ensure_initialized()`
2. If collection empty: warns, returns `[]`
3. `results = self._collection.query(query_texts=[question], n_results=min(n_results, count))`
4. Extracts `{content, source, distance}` for each result document
5. Returns list

**`get_context_for_step(intent, max_chars=3000) → str`:**
1. Calls `query(intent, n_results=3)`
2. If empty: returns `""`
3. Builds formatted string: header `"## Relevant Knowledge Base Context"`, then `"Source: {source}\n{content}"` for each result up to `max_chars` total
4. Returns joined with `"\n\n"`

**`_read_docx(path) → str`:** Opens with `DocxDocument`, joins non-empty paragraph texts with `"\n\n"`.

**`clear()`:** Deletes collection, recreates it with same name and cosine metadata.

---

# Part VIII — Utility Layer

## 8.1 File: `utils/dom_utils.py` (113 lines)

### Constants

**`KEEP_ATTRIBUTES`** — Set of 22 attribute names to preserve during HTML minification:
`id, class, name, type, value, placeholder, href, src, alt, title, role, aria-label, aria-labelledby, aria-describedby, data-testid, data-test, data-cy, for, action, method, disabled, checked, selected, readonly, required`

**`REMOVE_TAGS`** — Set of 7 tags to strip entirely: `script, style, noscript, svg, path, meta, link`

### Functions

**`minify_html(html, max_length=50000) → str`:**
1. Empty check: returns `""` if not html
2. **Remove noise tags:** For each tag in `REMOVE_TAGS`, two regex passes:
   - Opening+closing: `re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", ..., flags=re.DOTALL|re.IGNORECASE)`
   - Self-closing: `re.sub(rf"<{tag}[^>]*/?>", "", ..., flags=re.IGNORECASE)`
3. **Remove comments:** `re.sub(r"<!--.*?-->", "", ..., flags=re.DOTALL)`
4. **Filter attributes:** `re.sub(r"<(\w+)((?:\s+[^>]*?)?)(\s*/?)>", _filter_attributes, ...)` where `_filter_attributes`:
   - Extracts tag name, attributes string, closing slash
   - For each attribute match: keeps if `attr_name in KEEP_ATTRIBUTES or attr_name.startswith("data-test")`
   - Rebuilds tag with only kept attributes
5. **Collapse whitespace:** `re.sub(r"\s+", " ", ...)`, `re.sub(r">\s+<", "><", ...)`, `.strip()`
6. **Truncate:** If `len(result) > max_length`: truncate and append `"<!-- truncated -->"`

**`extract_interactive_elements(html) → str`:**
- Tags: `input, button, a, select, textarea, label, form, option`
- For each tag: `re.findall(rf"<{tag}[^>]*(?:>.*?</{tag}>|/>)", html, flags=re.DOTALL|re.IGNORECASE)`
- Returns `"\n".join(elements)`

**`extract_visible_text(html) → str`:**
- `re.sub(r"<[^>]+>", " ", html)` — strip tags
- `re.sub(r"\s+", " ", text)` — collapse whitespace
- `.strip()[:10000]` — truncate to 10,000 chars

## 8.2 File: `utils/screenshot_utils.py` (68 lines)

### Imports
`base64, io, pathlib.Path, typing.Optional, PIL.Image`

### Functions

**`screenshot_to_base64(screenshot_bytes: bytes) → str`:** `base64.b64encode(screenshot_bytes).decode("utf-8")`

**`base64_to_bytes(b64_string: str) → bytes`:** `base64.b64decode(b64_string)`

**`resize_screenshot(screenshot_bytes, max_width=1280, max_height=1024, quality=85) → bytes`:**
1. `img = Image.open(io.BytesIO(screenshot_bytes))`
2. If exceeds max dims: `img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)`
3. `img_rgb = img.convert("RGB")` — ensure RGB mode
4. `img_rgb.save(buffer, format="JPEG", quality=quality)`
5. Returns buffer bytes

**`save_screenshot(screenshot_bytes, output_dir, filename) → str`:**
1. `Path(output_dir).mkdir(parents=True, exist_ok=True)`
2. `file_path.write_bytes(screenshot_bytes)`
3. Returns `str(file_path)`

**`prepare_for_ai(screenshot_bytes, max_width=1280, max_height=1024) → str`:**
1. `resized = resize_screenshot(screenshot_bytes, max_width, max_height)`
2. `return screenshot_to_base64(resized)`

---

# Part IX — Cross-Cutting Concerns

## 9.1 Logging

All modules use `logger = logging.getLogger(__name__)`. Logging is configured in `main.py` via `RichHandler` with:
- Rich tracebacks enabled
- Console output to `rich.Console`
- Level configurable via `--log-level` CLI flag

Log levels used:
- `INFO`: Pipeline start/end, step progress, AI inference stats, artifact generation paths, config loading
- `WARNING`: Network idle timeouts, screenshot capture failures, fallback locator usage, empty RAG results
- `ERROR`: AI parsing failures, all-locators-exhausted, artifact generation failures

## 9.2 Error Handling Strategy

| Module | Error | Behavior |
|---|---|---|
| `main.py` | Missing URL or API keys | Print red error, `sys.exit(1)` |
| `RequirementParser` | File not found | Raise `FileNotFoundError` |
| `RequirementParser` | Unsupported format | Raise `ValueError` |
| `RequirementParser` | AI parsing failure per chunk | Log error, `continue` to next chunk |
| `LocatorEngine` | JSON decode error | Return `_fallback_locator()` |
| `LocatorEngine` | Any exception | Return `_fallback_locator()` |
| `ActionExecutor` | Locator timeout/error | Try next locator in ranked list |
| `ActionExecutor` | All locators fail | Mark step FAILED, continue to next step |
| `StateCaptureEngine` | Network idle timeout | Warn, proceed with current state |
| `StateCaptureEngine` | Element capture failure | Return `None` |
| `DocxGenerator` | Screenshot embed failure | Insert `[Screenshot could not be embedded: {exc}]` text |
| `Agent` | Artifact generation failure | Log error, continue (don't crash) |
| `RAGEngine` | Unsupported file format | Raise `ValueError` |

## 9.3 Security Model

- API keys stored only in `.env` (gitignored) and loaded via `python-dotenv`
- Keys never logged (logger never prints key values)
- `AppConfig` stores keys in memory only during runtime
- RAG vector store is local only (ChromaDB on disk at `output/vectorstore/`)
- Screenshots and DOM sent to external AI APIs over HTTPS

---

# Part X — Input & Test Data Layer

## 10.1 Directory: `input/requirements/` — 8 test data files

| File | Lines | Content |
|---|---|---|
| `TC001_valid_login.txt` | ~30 | 9-step login flow with standard_user |
| `TC002_invalid_login_scenarios.txt` | ~70 | 5 scenarios: wrong user, wrong pass, empty, empty pass, locked out |
| `TC003_product_browsing.txt` | ~90 | 5 scenarios: catalog display, sort low-high, sort high-low, sort Z-A, product details |
| `TC004_cart_management.txt` | ~80 | 5 scenarios: add single, add multiple, remove from cart, remove from page, continue shopping |
| `TC005_checkout_complete_flow.txt` | ~60 | 34-step E2E: login → add items → cart → checkout info → overview → confirm → back |
| `TC006_checkout_validation.txt` | ~50 | 4 scenarios: all empty, missing last name, missing zip, cancel |
| `TC007_sidebar_navigation.txt` | ~60 | 4 scenarios: open/close, all items, logout, reset app state |
| `TC008_edge_cases_and_performance.txt` | ~70 | 5 scenarios: performance user, error user, direct URL access, page refresh, all products |

## 10.2 Directory: `input/manuals/` — 2 knowledge base files

| File | Lines | Content |
|---|---|---|
| `saucedemo_app_manual.txt` | ~250 | Complete app reference: all 9 pages, every element ID/class/data-testid, sort options, navigation flow diagram |
| `saucedemo_test_credentials.txt` | ~60 | All 6 user accounts with behaviors, checkout data combos, product pricing, tax calculations |

## 10.3 Directory: `input/sample_data/` — 1 JSON file

`test_suite_full.json`: Structured JSON with `test_suite` metadata, `test_data` (valid users, invalid users, checkout info, products with prices), and 8 `test_cases` each with structured steps.

---

# Part XI — Dependency Map

## 11.1 Module Import Graph

```
main.py
├── core.agent.AutonomousTestAgent
│   ├── core.ai_engine.AIEngine
│   │   ├── anthropic
│   │   ├── google.generativeai
│   │   └── models.schemas.{AIProvider, AIRequest, AIResponse, AppConfig}
│   ├── core.locator_engine.LocatorEngine
│   │   ├── core.ai_engine.AIEngine
│   │   └── models.schemas.{AIProvider, Locator, LocatorSet, LocatorStrategy, PageState, TestStepInput}
│   ├── core.action_executor.ActionExecutor
│   │   ├── playwright.async_api.{Page, TimeoutError}
│   │   ├── models.schemas.{ActionType, Locator, LocatorSet, StepStatus, TestStepInput, TestStepResult}
│   │   └── utils.screenshot_utils.save_screenshot
│   ├── core.state_capture.StateCaptureEngine
│   │   ├── playwright.async_api.Page
│   │   ├── models.schemas.PageState
│   │   ├── utils.dom_utils.{extract_visible_text, minify_html}
│   │   └── utils.screenshot_utils.{prepare_for_ai, save_screenshot}
│   ├── core.requirement_parser.RequirementParser
│   │   ├── openpyxl
│   │   ├── docx.Document
│   │   ├── core.ai_engine.AIEngine
│   │   └── models.schemas.{ActionType, ParsedRequirements, RequirementItem, TestCase, TestStepInput}
│   ├── generators.script_generator.ScriptGenerator
│   │   └── models.schemas.{ActionType, LocatorSet, StepStatus, TestCase, TestCaseResult, TestStepResult}
│   ├── generators.docx_generator.DocxGenerator
│   │   ├── docx.{Document, enums, shared}
│   │   └── models.schemas.{StepStatus, TestCaseResult}
│   ├── generators.report_generator.ReportGenerator
│   │   └── models.schemas.{StepStatus, TestCaseResult}
│   ├── knowledge.rag_engine.RAGEngine
│   │   ├── chromadb (lazy)
│   │   ├── docx.Document
│   │   └── langchain_text_splitters.RecursiveCharacterTextSplitter
│   └── models.schemas.{AppConfig, StepStatus, TestCase, TestCaseResult, TestStepResult}
├── core.config_loader.load_config
│   ├── yaml
│   ├── dotenv.load_dotenv
│   └── models.schemas.{AIProvider, AppConfig}
└── rich.{Console, RichHandler, Panel, Table}
```

## 11.2 File Count & Line Count Summary

| Directory | Files | Total Lines | Purpose |
|---|---|---|---|
| `main.py` | 1 | 240 | CLI entry point |
| `core/` | 7 (+`__init__.py`) | 1,176 | Pipeline engines |
| `generators/` | 3 (+`__init__.py`) | 754 | Artifact generators |
| `knowledge/` | 1 (+`__init__.py`) | 171 | RAG knowledge base |
| `models/` | 1 (+`__init__.py`) | 285 | Pydantic data models |
| `utils/` | 2 (+`__init__.py`) | 181 | DOM + screenshot utilities |
| `config/` | 1 | 76 | YAML configuration |
| **Total Python** | **16 modules** | **~2,883 lines** | **Complete system** |

---

*End of Architecture Document — Version 1.0*
*Every module, class, method, field, constant, import, and algorithm in the codebase is documented above.*
