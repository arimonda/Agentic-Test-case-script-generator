# Self-Healing Autonomous Test Agent

# Technical Reference Manual

**Version 1.0 | February 2026**
**Confidential — Internal Use Only**

---

## Table of Contents

- [1. System Architecture](#1-system-architecture)
  - [1.1 Architecture Overview](#11-architecture-overview)
  - [1.2 Pipeline Stages](#12-pipeline-stages)
  - [1.3 Threading & Concurrency Model](#13-threading--concurrency-model)
  - [1.4 Data Flow Diagram](#14-data-flow-diagram)
  - [1.5 Technology Stack](#15-technology-stack)
- [2. Project Structure](#2-project-structure)
- [3. Core Module Reference](#3-core-module-reference)
  - [3.1 core/agent.py — AutonomousTestAgent](#31-coreagentpy--autonomoustestagent)
  - [3.2 core/ai_engine.py — AIEngine](#32-coreai_enginepy--aiengine)
  - [3.3 core/locator_engine.py — LocatorEngine](#33-corelocator_enginepy--locatorengine)
  - [3.4 core/action_executor.py — ActionExecutor](#34-coreaction_executorpy--actionexecutor)
  - [3.5 core/state_capture.py — StateCaptureEngine](#35-corestate_capturepy--statecaptureengine)
  - [3.6 core/requirement_parser.py — RequirementParser](#36-corerequirement_parserpy--requirementparser)
  - [3.7 core/config_loader.py — load_config()](#37-coreconfig_loaderpy--load_config)
- [4. Generator Module Reference](#4-generator-module-reference)
  - [4.1 generators/script_generator.py — ScriptGenerator](#41-generatorsscript_generatorpy--scriptgenerator)
  - [4.2 generators/docx_generator.py — DocxGenerator](#42-generatorsdocx_generatorpy--docxgenerator)
  - [4.3 generators/report_generator.py — ReportGenerator](#43-generatorsreport_generatorpy--reportgenerator)
- [5. Knowledge Module Reference](#5-knowledge-module-reference)
  - [5.1 knowledge/rag_engine.py — RAGEngine](#51-knowledgerag_enginepy--ragengine)
- [6. Utility Module Reference](#6-utility-module-reference)
  - [6.1 utils/dom_utils.py](#61-utilsdom_utilspy)
  - [6.2 utils/screenshot_utils.py](#62-utilsscreenshot_utilspy)
- [7. Data Models Reference](#7-data-models-reference)
  - [7.1 Enumerations](#71-enumerations)
  - [7.2 Locator Models](#72-locator-models)
  - [7.3 Test Step & Test Case Models](#73-test-step--test-case-models)
  - [7.4 Page State Model](#74-page-state-model)
  - [7.5 AI Request/Response Models](#75-ai-requestresponse-models)
  - [7.6 Configuration Model](#76-configuration-model)
- [8. Configuration Reference](#8-configuration-reference)
  - [8.1 Complete Settings Table](#81-complete-settings-table)
  - [8.2 Environment Variables](#82-environment-variables)
  - [8.3 Configuration Loading Logic](#83-configuration-loading-logic)
- [9. AI Provider Integration](#9-ai-provider-integration)
  - [9.1 Google Gemini Integration](#91-google-gemini-integration)
  - [9.2 Anthropic Claude Integration](#92-anthropic-claude-integration)
  - [9.3 Token Usage Analysis](#93-token-usage-analysis)
- [10. Prompt Engineering](#10-prompt-engineering)
  - [10.1 Locator Identification Prompt](#101-locator-identification-prompt)
  - [10.2 Requirement Parsing Prompt](#102-requirement-parsing-prompt)
  - [10.3 Prompt Design Principles](#103-prompt-design-principles)
- [11. Self-Healing Algorithm](#11-self-healing-algorithm)
  - [11.1 Algorithm Pseudocode](#111-algorithm-pseudocode)
  - [11.2 Locator Resolution](#112-locator-resolution)
  - [11.3 Supported Action Types](#113-supported-action-types)
- [12. DOM Processing Pipeline](#12-dom-processing-pipeline)
  - [12.1 HTML Minification](#121-html-minification)
  - [12.2 Interactive Element Extraction](#122-interactive-element-extraction)
  - [12.3 Screenshot Processing](#123-screenshot-processing)
- [13. CLI Architecture](#13-cli-architecture)
- [14. Extending the Agent](#14-extending-the-agent)
  - [14.1 Adding a New AI Provider](#141-adding-a-new-ai-provider)
  - [14.2 Adding a New Action Type](#142-adding-a-new-action-type)
  - [14.3 Adding a New Locator Strategy](#143-adding-a-new-locator-strategy)
  - [14.4 Custom Report Templates](#144-custom-report-templates)
  - [14.5 Adding a New Document Format](#145-adding-a-new-document-format)
- [15. Security Considerations](#15-security-considerations)
- [16. Performance Tuning](#16-performance-tuning)
- [17. Dependency Reference](#17-dependency-reference)

---

## 1. System Architecture

### 1.1 Architecture Overview

The system is a **pipeline-based autonomous agent** with five stages:

```
INGEST → CAPTURE → INFER → EXECUTE → GENERATE
```

Each stage is handled by a dedicated engine class, coordinated by a central `AutonomousTestAgent` orchestrator. The design follows separation of concerns — each engine can be tested and extended independently.

### 1.2 Pipeline Stages

| Stage | Engine | Input | Output |
|---|---|---|---|
| **1. INGEST** | `RequirementParser` | `.docx`, `.xlsx`, `.txt` | `list[TestCase]` |
| **2. CAPTURE** | `StateCaptureEngine` | Playwright `Page` | `PageState` |
| **3. INFER** | `LocatorEngine` + `AIEngine` | `PageState` + `TestStepInput` | `LocatorSet` |
| **4. EXECUTE** | `ActionExecutor` | `Page` + `LocatorSet` + `TestStepInput` | `TestStepResult` |
| **5. GENERATE** | `ScriptGenerator`, `DocxGenerator`, `ReportGenerator` | `TestCaseResult` | `.py`, `.docx`, `.html`, `.json` |

### 1.3 Threading & Concurrency Model

```
┌─────────────────────────────────────────────────┐
│  MAIN THREAD (asyncio event loop)               │
│                                                  │
│  • Playwright browser control                    │
│  • Page navigation & state capture               │
│  • AI inference calls (synchronous within async) │
│  • Action execution with self-healing            │
│                                                  │
│  ──── After all steps complete ────              │
│                                                  │
│  THREAD POOL (ThreadPoolExecutor, 3 workers)     │
│  ├─ Worker 1: ScriptGenerator.generate()         │
│  ├─ Worker 2: DocxGenerator.generate()           │
│  └─ Worker 3: ReportGenerator.generate()         │
└─────────────────────────────────────────────────┘
```

- **Main thread:** Runs the `asyncio` event loop for Playwright's async API. All browser interactions and AI API calls happen here sequentially.
- **Thread pool:** After test execution completes, three artifact generators run in parallel using `concurrent.futures.ThreadPoolExecutor` with 3 workers and a 30-second timeout per future.

### 1.4 Data Flow Diagram

```
RequirementFile (.docx/.xlsx/.txt)
        │
        ▼
RequirementParser ──(AI)──> list[TestCase]
        │                       │
        │                       ▼
        │               For each TestCase:
        │                       │
        │               ┌───────▼───────────┐
        │               │ Browser Page       │
        │               │ page.goto(url)     │
        │               └───────┬───────────┘
        │                       │
        │               For each TestStep:
        │                       │
        │               ┌───────▼───────────┐
        │               │ StateCaptureEngine │
        │               │ → PageState        │
        │               │   (screenshot +    │
        │               │    minified HTML)  │
        │               └───────┬───────────┘
        │                       │
 RAGEngine ──(context)──>  ┌────▼────────────┐
                           │ LocatorEngine    │
                           │ → LocatorSet     │
                           │   (3 ranked      │
                           │    locators)     │
                           └────┬────────────┘
                                │
                           ┌────▼────────────┐
                           │ ActionExecutor   │
                           │ → TestStepResult │
                           │   (self-healing) │
                           └────┬────────────┘
                                │
                        ┌───────▼──────────┐
                        │ TestCaseResult    │
                        │ (all step results)│
                        └───────┬──────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ScriptGenerator  DocxGenerator  ReportGenerator
           (.py)           (.docx)       (.html + .json)
```

### 1.5 Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.9+ | Core runtime |
| **Browser Automation** | Playwright 1.49+ | Browser control, screenshots, DOM |
| **AI (Gemini)** | google-generativeai 0.8+ | Multimodal inference (screenshot + text) |
| **AI (Claude)** | anthropic 0.42+ | Vision inference (base64 images + text) |
| **Data Validation** | Pydantic 2.10+ | Type-safe data models |
| **Document Parsing** | python-docx 1.1+, openpyxl 3.1+ | Read .docx and .xlsx files |
| **Document Generation** | python-docx 1.1+ | Write .docx test case documents |
| **Report Templates** | Jinja2 (inline HTML) | HTML execution reports |
| **Vector Database** | ChromaDB 0.5+ | RAG knowledge base storage |
| **Text Splitting** | langchain-text-splitters 0.3+ | Document chunking for RAG |
| **Image Processing** | Pillow 11.1+ | Screenshot resize and encoding |
| **Configuration** | PyYAML 6.0+, python-dotenv 1.0+ | YAML + .env configuration |
| **CLI** | argparse + rich 13.9+ | Command-line interface with rich output |
| **Retry Logic** | tenacity 9.0+ | Available for custom retry decorators |

---

## 2. Project Structure

```
Agentic Test case script generator/
│
├── main.py                         # CLI entry point — argument parsing, orchestration
│
├── config/
│   └── config.yaml                 # Runtime configuration (YAML)
│
├── core/                           # Core pipeline engines
│   ├── __init__.py
│   ├── agent.py                    # AutonomousTestAgent — central orchestrator
│   ├── ai_engine.py                # AIEngine — unified Gemini/Claude inference
│   ├── config_loader.py            # load_config() — YAML + .env merging
│   ├── locator_engine.py           # LocatorEngine — AI-driven element identification
│   ├── action_executor.py          # ActionExecutor — self-healing action execution
│   ├── requirement_parser.py       # RequirementParser — .docx/.xlsx/.txt parsing
│   └── state_capture.py            # StateCaptureEngine — screenshot + DOM capture
│
├── generators/                     # Artifact generation engines
│   ├── __init__.py
│   ├── script_generator.py         # Generates Python Playwright .py scripts
│   ├── docx_generator.py           # Generates Word .docx test case documents
│   └── report_generator.py         # Generates HTML + JSON execution reports
│
├── knowledge/                      # Knowledge base / RAG
│   ├── __init__.py
│   └── rag_engine.py               # RAGEngine — ChromaDB vector store
│
├── models/                         # Data models
│   ├── __init__.py
│   └── schemas.py                  # Pydantic models (15+ classes and enums)
│
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── dom_utils.py                # HTML minification and text extraction
│   └── screenshot_utils.py         # Screenshot resize, encode, save
│
├── input/                          # Test input files
│   ├── requirements/               # Requirement documents (.txt, .docx, .xlsx)
│   ├── manuals/                    # Knowledge base documents
│   └── sample_data/                # JSON test suite data
│
├── output/                         # Generated artifacts (created at runtime)
│   ├── scripts/
│   ├── testcases/
│   ├── reports/
│   ├── screenshots/
│   └── vectorstore/
│
├── docs/                           # Documentation
│   ├── USER_GUIDE.md
│   └── TECHNICAL_REFERENCE_MANUAL.md
│
├── create_sample_data.py           # Utility: generates sample .docx/.xlsx files
├── requirements.txt                # Python dependencies with pinned versions
├── .env.example                    # Environment variable template
├── .env                            # Active environment (not in Git)
├── .gitignore                      # Git exclusions
└── README.md                       # Project overview
```

---

## 3. Core Module Reference

### 3.1 `core/agent.py` — AutonomousTestAgent

The central orchestrator class that wires together all subsystems.

**Class:** `AutonomousTestAgent`

**Constructor:**
```python
AutonomousTestAgent(config: AppConfig)
```

Initializes:
- `AIEngine` — from `config.gemini_api_key` / `config.claude_api_key`
- `LocatorEngine` — wraps `AIEngine`
- `StateCaptureEngine` — output dir = `{config.output_dir}/screenshots`
- `ActionExecutor` — `max_retries=config.max_healing_retries`, `action_timeout=config.timeout`
- `RequirementParser` — wraps `AIEngine`
- `RAGEngine` — if `config.rag_enabled`, persist dir = `{config.output_dir}/vectorstore`
- `ScriptGenerator`, `DocxGenerator`, `ReportGenerator` — separate output subdirectories
- `ThreadPoolExecutor(max_workers=3)` — for parallel artifact generation

**Public Methods:**

| Method | Signature | Returns | Description |
|---|---|---|---|
| `run` | `async run(requirement_file=None, requirement_text=None, target_url=None, knowledge_dir=None)` | `list[TestCaseResult]` | Full pipeline: parse → execute → generate |
| `run_single_step` | `async run_single_step(target_url, intent, action_type="click", input_data=None)` | `TestStepResult` | Execute one step (demo mode) |

**Pipeline flow in `run()`:**
1. If `knowledge_dir` provided and RAG enabled: `rag_engine.ingest_directory(knowledge_dir)`
2. Parse requirements: `_parse_requirements(file, text, url)` → `list[TestCase]`
3. Launch Playwright: `async_playwright()` → `chromium.launch()` → `browser.new_context()`
4. For each `TestCase`: `_execute_test_case(context, test_case)` → `TestCaseResult`
5. Close browser
6. `_generate_artifacts_parallel(results)` — submits to thread pool

**Internal method `_execute_test_case()`:**
1. Open new page: `context.new_page()`
2. Navigate to `test_case.target_url`
3. For each step:
   - `state_capture.capture(page, label)` → `PageState`
   - `rag_engine.get_context_for_step(step.intent)` (if RAG enabled)
   - `locator_engine.identify_locators(state, step)` → `LocatorSet`
   - `report_gen.log_ai_usage(...)` — record for HTML report
   - `action_executor.execute_step(page, step, locators)` → `TestStepResult`
4. Compute overall status: FAILED if any failed, HEALED if any healed, else PASSED
5. Close page

### 3.2 `core/ai_engine.py` — AIEngine

Unified multi-model inference engine with provider dispatch.

**Class:** `AIEngine`

**Constructor:**
```python
AIEngine(config: AppConfig)
```
Calls `_init_providers()` which:
- If `config.gemini_api_key`: calls `genai.configure(api_key=...)`
- If `config.claude_api_key`: creates `anthropic.Anthropic(api_key=...)`

**Public Methods:**

| Method | Signature | Returns | Description |
|---|---|---|---|
| `infer` | `infer(prompt, images=None, provider=None, temperature=None, max_tokens=None)` | `AIResponse` | Core inference — dispatches to Gemini or Claude |
| `infer_json` | `infer_json(prompt, images=None, provider=None)` | `dict` | Calls `infer()` + strips markdown fences + `json.loads()` |

**Provider dispatch in `infer()`:**
- Constructs `AIRequest` with model name from `_get_model_name(provider, has_images)`
- If GEMINI: calls `_infer_gemini(request)`
- If CLAUDE: calls `_infer_claude(request)`
- Measures latency with `time.perf_counter()`

**Gemini implementation (`_infer_gemini`):**
- Uses `genai.GenerativeModel(model_name)`
- Constructs multi-part content: `[{mime_type, data}, ..., prompt_text]`
- Uses `GenerationConfig(temperature, max_output_tokens)`
- Extracts usage metadata (`prompt_token_count`, `candidates_token_count`, `total_token_count`)

**Claude implementation (`_infer_claude`):**
- Constructs content blocks: `[{type: "image", source: {type: "base64", ...}}, {type: "text", text: prompt}]`
- Calls `client.messages.create(model, max_tokens, temperature, messages)`
- Extracts `response.usage.input_tokens` and `output_tokens`

**Model selection (`_get_model_name`):**
- GEMINI + images → `config.gemini_vision_model`
- GEMINI + text only → `config.gemini_text_model`
- CLAUDE + images → `config.claude_vision_model`
- CLAUDE + text only → `config.claude_text_model`

### 3.3 `core/locator_engine.py` — LocatorEngine

AI-driven element identification with structured prompt engineering.

**Class:** `LocatorEngine`

**Constructor:**
```python
LocatorEngine(ai_engine: AIEngine)
```

**Public Methods:**

| Method | Signature | Returns | Description |
|---|---|---|---|
| `identify_locators` | `identify_locators(page_state, step, provider=None)` | `LocatorSet` | Single element identification |
| `identify_multiple_locators` | `identify_multiple_locators(page_state, steps)` | `list[LocatorSet]` | Batch identification |

**Prompt construction in `identify_locators()`:**
- Uses `LOCATOR_PROMPT_TEMPLATE` with variables: `intent`, `action_type`, `input_data`, `url`, `title`, `html_snippet` (first 15,000 chars of minified HTML)
- Attaches `page_state.screenshot_base64` as image
- Calls `ai.infer_json(prompt, images)`
- Parses response into `LocatorSet` via `_parse_locator_response()`
- On failure: returns `_fallback_locator()` — a visual text-based locator with 0.3 confidence

**Locator priority enforced by prompt:** `data-testid > id > aria-label > CSS > XPath > visual text`

### 3.4 `core/action_executor.py` — ActionExecutor

Self-healing browser action execution.

**Class:** `ActionExecutor`

**Constructor:**
```python
ActionExecutor(max_retries=3, action_timeout=10000, output_dir="output/screenshots")
```

**Public Methods:**

| Method | Signature | Returns | Description |
|---|---|---|---|
| `execute_step` | `async execute_step(page, step, locators)` | `TestStepResult` | Execute with self-healing fallback |

**Self-healing algorithm:**
```
1. Capture before-screenshot
2. Get ranked locators: [primary, secondary, tertiary] (skip None)
3. For idx, locator in enumerate(ranked):
     a. Log: "Trying {strategy} locator ({value})"
     b. resolve_locator(page, locator) → Playwright locator object
     c. wait_for(visible, timeout)
     d. perform_action(page, step, locator)
     e. If success:
          - If idx == 0: status = PASSED
          - If idx > 0: status = HEALED
          - Break
     f. If exception:
          - Log warning
          - Continue to next locator
4. If all failed:
     - status = FAILED
     - error_message = last error
5. Capture after-screenshot
6. Record duration_ms
```

**Locator resolution (`_resolve_locator`):**

| Strategy | Playwright API |
|---|---|
| `test_id` | `page.get_by_test_id(value)` |
| `id` | `page.locator(f"#{value}")` |
| `aria` | `page.get_by_label(value)` or `page.get_by_role(role, name=name)` if `=` in value |
| `css` | `page.locator(value)` |
| `xpath` | `page.locator(value)` |
| `visual` | `page.get_by_text(value)` |

**Action execution (`_perform_action`):**

| ActionType | Playwright Code |
|---|---|
| `click` | `locator.click(timeout=...)` |
| `fill` | `locator.fill(input_data, timeout=...)` |
| `select` | `locator.select_option(input_data, timeout=...)` |
| `check` | `locator.check(timeout=...)` |
| `uncheck` | `locator.uncheck(timeout=...)` |
| `hover` | `locator.hover(timeout=...)` |
| `navigate` | `page.goto(url, wait_until="networkidle")` |
| `wait` | `page.wait_for_timeout(ms)` |
| `assert_visible` | `locator.wait_for(state="visible", timeout=...)` |
| `assert_text` | `locator.text_content()` → case-insensitive `in` check |
| `assert_value` | `locator.input_value()` → exact match check |
| `screenshot` | No-op (screenshots captured automatically) |

### 3.5 `core/state_capture.py` — StateCaptureEngine

Captures complete page state for AI analysis.

**Class:** `StateCaptureEngine`

**Constructor:**
```python
StateCaptureEngine(output_dir="output/screenshots")
```

**Public Methods:**

| Method | Signature | Returns | Description |
|---|---|---|---|
| `capture` | `async capture(page, step_label="page", full_page=True)` | `PageState` | Full page snapshot |
| `capture_element` | `async capture_element(page, selector, label="element")` | `bytes \| None` | Single element screenshot |

**`capture()` workflow:**
1. `page.wait_for_load_state("networkidle", timeout=10000)` — with fallback on timeout
2. `page.screenshot(full_page=full_page)` → raw PNG bytes
3. `save_screenshot(bytes, dir, filename)` → file path
4. `prepare_for_ai(bytes)` → resize to 1280x1024 max → base64 encode
5. `page.content()` → raw DOM HTML
6. `minify_html(dom_html)` → stripped HTML (max 50,000 chars)
7. `extract_visible_text(dom_html)` → plain text (max 10,000 chars)
8. Assemble `PageState(url, title, screenshot_path, screenshot_base64, dom_html, minified_html, visible_text)`

### 3.6 `core/requirement_parser.py` — RequirementParser

Document parsing with AI-powered structuring.

**Class:** `RequirementParser`

**Constructor:**
```python
RequirementParser(ai_engine: AIEngine)
```

**Public Methods:**

| Method | Signature | Returns | Description |
|---|---|---|---|
| `parse_file` | `parse_file(file_path, target_url="")` | `list[TestCase]` | Parse .docx or .xlsx |
| `parse_text` | `parse_text(text, target_url="")` | `list[TestCase]` | Parse raw text |

**Document extraction:**
- `.docx` (`_extract_docx`): Reads all `doc.paragraphs[].text` + all `doc.tables[].rows[].cells[].text` joined by ` | `
- `.xlsx` (`_extract_xlsx`): Reads all sheets. Row 1 = headers. Subsequent rows formatted as `Header: Value; Header: Value; ...`

**AI parsing (`_ai_parse`):**
1. Chunk text into 8,000-char segments via `_chunk_text()`
2. For each chunk: format `PARSE_PROMPT_TEMPLATE` and call `ai.infer_json(prompt)`
3. Extract `steps[]` from response, convert `action_type` string to `ActionType` enum
4. Assemble `TestCase` with `name`, `description`, `preconditions`, `target_url`, `steps`

### 3.7 `core/config_loader.py` — load_config()

**Function:**
```python
load_config(config_path="config/config.yaml", env_path=".env") → AppConfig
```

**Loading order:**
1. `load_dotenv(env_path)` — loads `.env` into environment
2. `yaml.safe_load(config_path)` — reads YAML structure
3. Resolves each setting: `os.getenv(ENV_VAR)` → YAML value → default
4. Returns validated `AppConfig` Pydantic model

---

## 4. Generator Module Reference

### 4.1 `generators/script_generator.py` — ScriptGenerator

**Class:** `ScriptGenerator`

**Constructor:**
```python
ScriptGenerator(output_dir="output/scripts")
```

**Public Methods:**

| Method | Returns | Description |
|---|---|---|
| `generate(test_result: TestCaseResult)` | `str` (file path) | Generate `.py` file |

**Script structure:**
```python
"""Auto-Generated Playwright Test Script..."""
import re
from playwright.sync_api import Playwright, sync_playwright, expect

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    page.goto("target_url")
    page.wait_for_load_state("networkidle")

    # Step 1: intent
    # Expected: expected_result
    # Element: element_name
    page.locator("#primary").click()
    # --- Backup locators ---
    # Backup 2 (aria): page.get_by_label("...")
    # Backup 3 (xpath): page.locator("//...")

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
```

Generates `sync_playwright` API (not async) for standalone runnability.

### 4.2 `generators/docx_generator.py` — DocxGenerator

**Class:** `DocxGenerator`

**Constructor:**
```python
DocxGenerator(output_dir="output/testcases")
```

**Document sections:**
1. **Title** — centered heading with timestamp subtitle
2. **Metadata table** — 2-column table with ID, description, preconditions, URL, source, step count, status
3. **Steps table** — 6-column table (Step #, Action, Input Data, Expected Result, Status, Locator) with color-coded status cells
4. **Screenshots section** — heading per step, embedded before/after PNGs at 5.5" width
5. **Summary section** — bullet list with pass/fail/heal counts, duration, healing attempts

**Status colors:**
- PASSED: RGB(0, 150, 0) green
- FAILED: RGB(200, 0, 0) red
- HEALED: RGB(200, 150, 0) amber

### 4.3 `generators/report_generator.py` — ReportGenerator

**Class:** `ReportGenerator`

**Constructor:**
```python
ReportGenerator(output_dir="output/reports")
```

**Public Methods:**

| Method | Description |
|---|---|
| `log_ai_usage(step_number, provider, tokens, latency_ms, reasoning)` | Record AI metrics (called during execution) |
| `generate(test_result: TestCaseResult) → str` | Generate HTML + JSON reports |

**HTML report features:**
- Dark theme (CSS custom properties: `--bg: #0f172a`, `--surface: #1e293b`)
- CSS Grid statistics cards (total, passed, failed, healed, duration, tokens)
- Step cards with badge status, locator info, error details
- AI usage table (step, provider, tokens, latency, reasoning)
- Responsive layout

**JSON report structure:**
```json
{
  "test_case": { ... TestCase model dump ... },
  "step_results": [ ... TestStepResult model dumps ... ],
  "summary": {
    "overall_status": "passed",
    "passed": 5, "failed": 0, "healed": 1,
    "total_duration_ms": 12340.5,
    "total_healing_attempts": 1
  },
  "ai_usage": [
    {"step": 1, "provider": "GEMINI", "tokens": 3200, "latency_ms": 1500, "reasoning": "..."}
  ]
}
```

---

## 5. Knowledge Module Reference

### 5.1 `knowledge/rag_engine.py` — RAGEngine

Local vector-based RAG engine.

**Class:** `RAGEngine`

**Constructor:**
```python
RAGEngine(persist_dir="output/vectorstore", chunk_size=1000, chunk_overlap=200, collection_name="knowledge_base")
```

**Lazy initialization:** `_ensure_initialized()` creates `chromadb.PersistentClient` and collection on first use.

**Public Methods:**

| Method | Signature | Returns | Description |
|---|---|---|---|
| `ingest_document` | `ingest_document(file_path)` | `int` (chunks) | Ingest a single .docx/.txt/.md file |
| `ingest_directory` | `ingest_directory(dir_path)` | `int` (total chunks) | Ingest all supported files in directory |
| `query` | `query(question, n_results=5)` | `list[dict]` | Semantic search, returns `{content, source, distance}` |
| `get_context_for_step` | `get_context_for_step(intent, max_chars=3000)` | `str` | Formatted RAG context for AI prompt |
| `clear` | `clear()` | `None` | Delete and recreate collection |

**Chunking:** Uses `langchain_text_splitters.RecursiveCharacterTextSplitter` with separators `["\n\n", "\n", ". ", " ", ""]`.

**Storage:** ChromaDB `PersistentClient` with cosine similarity (`hnsw:space: cosine`). Uses `collection.upsert()` for idempotent ingestion.

---

## 6. Utility Module Reference

### 6.1 `utils/dom_utils.py`

Three functions for HTML processing:

**`minify_html(html, max_length=50000) → str`**
1. Remove tags in `REMOVE_TAGS`: `script`, `style`, `noscript`, `svg`, `path`, `meta`, `link`
2. Remove HTML comments
3. Strip attributes not in `KEEP_ATTRIBUTES` (preserves `id`, `class`, `name`, `type`, `value`, `placeholder`, `href`, `role`, `aria-*`, `data-testid`, `data-test`, `data-cy`, etc.)
4. Collapse whitespace
5. Truncate to `max_length`

**`extract_interactive_elements(html) → str`**
Returns only `input`, `button`, `a`, `select`, `textarea`, `label`, `form`, `option` elements.

**`extract_visible_text(html) → str`**
Strips all tags, collapses whitespace, returns first 10,000 characters.

### 6.2 `utils/screenshot_utils.py`

**`screenshot_to_base64(bytes) → str`** — Encode raw bytes to base64.

**`resize_screenshot(bytes, max_width=1280, max_height=1024, quality=85) → bytes`** — Resize preserving aspect ratio, output as JPEG.

**`save_screenshot(bytes, output_dir, filename) → str`** — Write to disk, return file path.

**`prepare_for_ai(bytes, max_width=1280, max_height=1024) → str`** — Resize + base64 encode in one call.

---

## 7. Data Models Reference

All models in `models/schemas.py` using Pydantic v2.

### 7.1 Enumerations

```python
class LocatorStrategy(str, Enum):
    TEST_ID = "test_id"    # data-testid attributes
    ID = "id"              # HTML id
    ARIA = "aria"          # ARIA labels/roles
    CSS = "css"            # CSS selectors
    XPATH = "xpath"        # XPath expressions
    VISUAL = "visual"      # Visual text matching

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
```

### 7.2 Locator Models

**`Locator`** — Single element locator with AI confidence score.
- `strategy: LocatorStrategy`
- `value: str`
- `confidence: float` (0.0–1.0)
- `description: str`
- Method: `to_playwright() → str` — returns Python code string

**`LocatorSet`** — Ranked set of 1–3 locators.
- `element_name: str`
- `element_description: str`
- `primary: Locator`
- `secondary: Optional[Locator]`
- `tertiary: Optional[Locator]`
- Method: `ranked() → list[Locator]` — returns non-None locators in priority order

### 7.3 Test Step & Test Case Models

**`TestStepInput`** — Pre-execution step definition.
- `step_number: int`, `intent: str`, `action_type: ActionType`, `input_data: Optional[str]`, `expected_result: str`, `page_url: Optional[str]`

**`TestStepResult`** — Post-execution step result.
- `step_id: str` (auto UUID), `step_input: TestStepInput`, `status: StepStatus`, `locators_used: Optional[LocatorSet]`, `locator_used_index: int`, `screenshot_before/after: Optional[str]`, `actual_result: str`, `error_message: str`, `healing_attempts: int`, `duration_ms: float`, `ai_reasoning: str`, `timestamp: datetime`

**`TestCase`** — Collection of steps with metadata.
- `id: str` (auto UUID), `name: str`, `description: str`, `preconditions: str`, `target_url: str`, `steps: list[TestStepInput]`, `tags: list[str]`, `source_file: Optional[str]`, `created_at: datetime`

**`TestCaseResult`** — Full execution results.
- `test_case: TestCase`, `step_results: list[TestStepResult]`, `overall_status: StepStatus`, `total_duration_ms: float`, `total_healing_attempts: int`, `started_at/completed_at: Optional[datetime]`
- Properties: `passed_steps`, `failed_steps`, `healed_steps` (computed from step_results)

### 7.4 Page State Model

**`PageState`** — Snapshot of a web page at a point in time.
- `url: str`, `title: str`, `screenshot_path: str`, `screenshot_base64: Optional[str]`, `dom_html: str`, `minified_html: str`, `visible_text: str`, `timestamp: datetime`

### 7.5 AI Request/Response Models

**`AIRequest`** — `provider`, `model`, `prompt`, `images: list[str]`, `temperature`, `max_tokens`

**`AIResponse`** — `provider`, `model`, `content: str`, `usage: dict`, `latency_ms: float`, `raw_response`

### 7.6 Configuration Model

**`AppConfig`** — 30+ fields covering AI, Playwright, self-healing, artifacts, RAG, and model settings.

---

## 8. Configuration Reference

### 8.1 Complete Settings Table

| Setting | YAML Path | Env Variable | Default | Type |
|---|---|---|---|---|
| AI Provider | `ai_provider` | `AI_PROVIDER` | `GEMINI` | str |
| Gemini API Key | `api_keys.gemini` | `GEMINI_API_KEY` | `""` | str |
| Claude API Key | `api_keys.claude` | `CLAUDE_API_KEY` | `""` | str |
| OpenAI API Key | — | `OPENAI_API_KEY` | `""` | str |
| Target URL | — | `TARGET_URL` | `""` | str |
| Gemini Vision Model | `models.gemini.vision_model` | — | `gemini-2.5-flash` | str |
| Gemini Text Model | `models.gemini.text_model` | — | `gemini-2.5-flash` | str |
| Claude Vision Model | `models.claude.vision_model` | — | `claude-sonnet-4-20250514` | str |
| Claude Text Model | `models.claude.text_model` | — | `claude-sonnet-4-20250514` | str |
| Max Tokens | `models.*.max_tokens` | — | `4096` | int |
| Temperature | `models.*.temperature` | — | `0.2` | float |
| Headless | `playwright.headless` | — | `false` | bool |
| Browser | `playwright.browser` | — | `chromium` | str |
| Screenshot Type | `playwright.screenshot_type` | — | `full_page` | str |
| Viewport Width | `playwright.viewport.width` | — | `1920` | int |
| Viewport Height | `playwright.viewport.height` | — | `1080` | int |
| Action Timeout | `playwright.timeout` | — | `30000` | int (ms) |
| Navigation Timeout | `playwright.navigation_timeout` | — | `60000` | int (ms) |
| Retries | `playwright.retries` | — | `3` | int |
| Slow Mo | `playwright.slow_mo` | — | `100` | int (ms) |
| Self-Healing Enabled | `self_healing.enabled` | — | `true` | bool |
| Max Healing Retries | `self_healing.max_retries` | — | `3` | int |
| Output Directory | `artifacts.output_dir` | — | `output` | str |
| Generate Script | `artifacts.generate_script` | — | `true` | bool |
| Generate DOCX | `artifacts.generate_docx` | — | `true` | bool |
| Generate Report | `artifacts.generate_report` | — | `true` | bool |
| Report Format | `artifacts.report_format` | — | `html` | str |
| RAG Enabled | `rag.enabled` | — | `true` | bool |
| Chunk Size | `rag.chunk_size` | — | `1000` | int |
| Chunk Overlap | `rag.chunk_overlap` | — | `200` | int |
| Log Level | `logging.level` | `LOG_LEVEL` | `INFO` | str |

### 8.2 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes (if using Gemini) | Google AI Studio API key |
| `CLAUDE_API_KEY` | Yes (if using Claude) | Anthropic API key |
| `OPENAI_API_KEY` | No | For premium RAG embeddings |
| `TARGET_URL` | No | Default target application URL |
| `AI_PROVIDER` | No | Override default AI provider |
| `LOG_LEVEL` | No | Override logging verbosity |

### 8.3 Configuration Loading Logic

```
1. load_dotenv(".env")                    # Inject env vars
2. yaml.safe_load("config/config.yaml")   # Read YAML
3. For each setting:
   value = os.getenv(ENV_VAR) ?? yaml_config[path] ?? default
4. Return AppConfig(**values)              # Validate via Pydantic
```

---

## 9. AI Provider Integration

### 9.1 Google Gemini Integration

| Property | Value |
|---|---|
| SDK | `google-generativeai` |
| Auth | `genai.configure(api_key=key)` |
| Model class | `genai.GenerativeModel(model_name)` |
| Image input | `{"mime_type": "image/jpeg", "data": raw_bytes}` |
| Config | `genai.types.GenerationConfig(temperature, max_output_tokens)` |
| Call | `model.generate_content(parts, generation_config)` |
| Response text | `response.text` |
| Usage | `response.usage_metadata.{prompt_token_count, candidates_token_count, total_token_count}` |

### 9.2 Anthropic Claude Integration

| Property | Value |
|---|---|
| SDK | `anthropic` |
| Auth | `anthropic.Anthropic(api_key=key)` |
| Image input | `{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64_str}}` |
| Call | `client.messages.create(model, max_tokens, temperature, messages)` |
| Response text | `response.content[0].text` |
| Usage | `response.usage.{input_tokens, output_tokens}` |

### 9.3 Token Usage Analysis

| Component | Gemini Tokens | Claude Tokens |
|---|---|---|
| Minified HTML (avg page) | 800–1,500 | 800–1,500 |
| Locator prompt template | ~800 | ~800 |
| Screenshot (image) | ~1,000–2,000 | ~1,500–2,500 |
| Response (JSON locators) | ~300–500 | ~300–500 |
| **Per step total** | **~2,900–4,800** | **~3,400–5,300** |
| **10-step test total** | **~29,000–48,000** | **~34,000–53,000** |

---

## 10. Prompt Engineering

### 10.1 Locator Identification Prompt

The core prompt in `locator_engine.py` follows this structure:

```
ROLE: "You are an expert Playwright test automation engineer."

TASK: "Analyze the provided screenshot and HTML to identify the UI element."

TARGET: Intent, action type, input data

CONTEXT: URL, page title

HTML: Minified HTML (up to 15,000 chars)

FORMAT: Strict JSON schema with primary/secondary/tertiary locators,
        each having strategy, value, confidence, description

RULE: "Prioritize: data-testid > id > aria-label > CSS > XPath > visual text"
```

### 10.2 Requirement Parsing Prompt

The parsing prompt in `requirement_parser.py`:

```
ROLE: "You are an expert QA analyst."

TASK: "Parse the following requirement text into structured test steps."

INPUT: Raw requirement text (up to 8,000 chars per chunk)

FORMAT: JSON with test_case_name, description, preconditions, steps[]

RULES:
- Break complex requirements into atomic steps
- Start with navigation if URL mentioned
- Include assertion steps
- Use specific action_type values
- Put data in input_data field
```

### 10.3 Prompt Design Principles

1. **Structured output** — Always request specific JSON schema
2. **No markdown fences** — Explicitly say "Return ONLY valid JSON (no markdown fences)"
3. **Priority guidance** — Tell the AI which locator strategies to prefer
4. **Context limits** — Cap HTML at 15,000 chars, text at 8,000 chars per chunk
5. **Fallback handling** — `infer_json()` strips markdown code fences if the AI includes them despite instructions

---

## 11. Self-Healing Algorithm

### 11.1 Algorithm Pseudocode

```
function execute_step(page, step, locator_set):
    before_screenshot = capture(page)
    ranked_locators = locator_set.ranked()  # [primary, secondary?, tertiary?]
    
    for idx, locator in enumerate(ranked_locators):
        try:
            pw_locator = resolve(page, locator)
            pw_locator.wait_for(visible, timeout)
            perform_action(pw_locator, step.action_type, step.input_data)
            
            status = PASSED if idx == 0 else HEALED
            return TestStepResult(status, healing_attempts=idx)
        except:
            continue
    
    return TestStepResult(FAILED, error=last_exception)
```

### 11.2 Locator Resolution

See Section 3.4 — ActionExecutor `_resolve_locator()` table.

### 11.3 Supported Action Types

See Section 3.4 — ActionExecutor `_perform_action()` table (13 action types).

---

## 12. DOM Processing Pipeline

### 12.1 HTML Minification

Input: Raw `page.content()` (typically 50,000–500,000 chars)
Output: Clean HTML (typically 5,000–50,000 chars)

Steps:
1. Remove `<script>`, `<style>`, `<noscript>`, `<svg>`, `<path>`, `<meta>`, `<link>` tags + content
2. Remove HTML comments `<!-- ... -->`
3. Strip attributes not in whitelist (keeps: `id`, `class`, `name`, `type`, `value`, `placeholder`, `href`, `src`, `alt`, `title`, `role`, `aria-*`, `data-testid`, `data-test`, `data-cy`, `for`, `action`, `method`, `disabled`, `checked`, `selected`, `readonly`, `required`)
4. Collapse all whitespace
5. Remove whitespace between tags
6. Truncate to 50,000 chars

### 12.2 Interactive Element Extraction

Extracts only: `<input>`, `<button>`, `<a>`, `<select>`, `<textarea>`, `<label>`, `<form>`, `<option>`

Used for focused analysis when full minified HTML is too large.

### 12.3 Screenshot Processing

1. Full-page PNG captured via Playwright
2. Saved to disk as `{label}_{timestamp}.png`
3. For AI: resized to max 1280x1024 (preserving aspect ratio) → converted to JPEG (quality 85) → base64 encoded

---

## 13. CLI Architecture

Entry point: `main.py`

```
main.py
├── parse_args() → argparse.Namespace
├── setup_logging() → Rich-formatted console logging
├── display_banner() → Rich Panel
├── load_config() → AppConfig (with CLI overrides applied)
├── AutonomousTestAgent(config)
│   ├── if --demo: agent.run_single_step()
│   └── else: agent.run()
└── display_results() → Rich Table
```

---

## 14. Extending the Agent

### 14.1 Adding a New AI Provider

1. Add to `AIProvider` enum in `models/schemas.py`: `OPENAI = "OPENAI"`
2. Add config fields to `AppConfig`: `openai_vision_model`, etc.
3. In `core/ai_engine.py`:
   - Add initialization in `_init_providers()`
   - Add `_infer_openai(request)` method
   - Add case in `infer()` dispatch
   - Add case in `_get_model_name()`
4. Add config in `config.yaml` under `models.openai`
5. Add env var support in `config_loader.py`
6. Add `--provider OPENAI` choice in `main.py` argparse

### 14.2 Adding a New Action Type

1. Add to `ActionType` enum: `DOUBLE_CLICK = "double_click"`
2. In `ActionExecutor._perform_action()`: add `case ActionType.DOUBLE_CLICK: await pw_locator.dblclick()`
3. In `ScriptGenerator._build_action_code()`: add `case ActionType.DOUBLE_CLICK: return f"    {loc_code}.dblclick()"`
4. Update the `PARSE_PROMPT_TEMPLATE` in `requirement_parser.py` to include the new action type

### 14.3 Adding a New Locator Strategy

1. Add to `LocatorStrategy` enum: `NAME = "name"`
2. In `Locator.to_playwright()`: add `case LocatorStrategy.NAME: return f'page.locator("[name={self.value}]")'`
3. In `ActionExecutor._resolve_locator()`: add `case LocatorStrategy.NAME: return page.locator(f"[name={locator.value}]")`
4. Update `LOCATOR_PROMPT_TEMPLATE` to mention the new strategy
5. Add to `self_healing.locator_strategies` in `config.yaml`

### 14.4 Custom Report Templates

Edit the `HTML_TEMPLATE` string constant in `generators/report_generator.py`. The template uses Python `.format()` with these variables:
- `{test_name}`, `{description}`, `{timestamp}`
- `{total_steps}`, `{passed}`, `{failed}`, `{healed}`, `{duration}`, `{total_tokens}`
- `{step_cards}` — HTML string built from `STEP_CARD_TEMPLATE`
- `{ai_log_rows}` — HTML table rows

### 14.5 Adding a New Document Format

To support `.pdf` requirements:
1. Add a dependency (e.g., `pymupdf` or `pdfplumber`) to `requirements.txt`
2. In `RequirementParser.parse_file()`: add `elif ext == ".pdf": raw_text = self._extract_pdf(path)`
3. Implement `_extract_pdf(path)` method

---

## 15. Security Considerations

### API Key Protection
- `.env` excluded from Git via `.gitignore`
- Keys loaded via `python-dotenv`, never hardcoded
- `AppConfig` stores keys in memory only during runtime
- Logs never print API key values

### Data in Transit
- Screenshots and DOM content sent to AI APIs over HTTPS
- Contains potentially sensitive application data
- Ensure compliance with data handling policies before testing production apps

### Generated Artifacts
- Screenshots in `output/screenshots/` may contain PII visible on the page
- Word documents embed these screenshots
- HTML reports contain step details
- Secure the `output/` directory appropriately

### RAG Vector Store
- ChromaDB stores on local disk only (`output/vectorstore/`)
- No external API calls for embedding (uses built-in model)
- Contains chunked text from ingested documents

---

## 16. Performance Tuning

### Reducing Latency

| Technique | How | Impact |
|---|---|---|
| Use Gemini | `--provider GEMINI` | 2–3x faster inference |
| Headless mode | `--headless` | 10–20% faster |
| Reduce slow_mo | `playwright.slow_mo: 0` | No artificial delays |
| Smaller viewport | `viewport: {width: 1280, height: 720}` | Smaller screenshots |
| Lower max_tokens | `models.*.max_tokens: 2048` | Shorter AI responses |

### Reducing Cost

| Technique | How | Impact |
|---|---|---|
| Auto-minification | Built-in (always active) | ~70% HTML reduction |
| Screenshot resize | Built-in (1280x1024 max) | ~50% image size reduction |
| Disable RAG | `rag.enabled: false` | Skip embedding cost |
| Use Gemini | Default provider | Cheaper per token |

### Increasing Reliability

| Technique | How | Impact |
|---|---|---|
| More retries | `self_healing.max_retries: 5` | More healing chances |
| Longer timeout | `playwright.timeout: 60000` | Handles slow apps |
| Use RAG | `-k input/manuals/` | Better locator accuracy |
| Add slow_mo | `playwright.slow_mo: 200` | More time for page to settle |

---

## 17. Dependency Reference

| Package | Version | Purpose |
|---|---|---|
| `playwright` | 1.49.1 | Browser automation |
| `anthropic` | 0.42.0 | Claude API client |
| `google-generativeai` | 0.8.4 | Gemini API client |
| `python-docx` | 1.1.2 | Read/write Word documents |
| `openpyxl` | 3.1.5 | Read Excel spreadsheets |
| `chromadb` | 0.5.23 | Vector database for RAG |
| `langchain-text-splitters` | 0.3.4 | Document chunking |
| `Pillow` | 11.1.0 | Image processing |
| `PyYAML` | 6.0.2 | YAML configuration parsing |
| `python-dotenv` | 1.0.1 | .env file loading |
| `pydantic` | 2.10.4 | Data model validation |
| `jinja2` | 3.1.5 | Template rendering |
| `rich` | 13.9.4 | Terminal formatting |
| `tenacity` | 9.0.0 | Retry decorators |
| `aiofiles` | 24.1.0 | Async file operations |

---

*End of Technical Reference Manual — Version 1.0*
