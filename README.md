# Self-Healing Autonomous Test Agent

An AI-powered automated testing ecosystem that integrates **Computer Vision**, **Large Language Models (LLMs)**, and **Playwright** into a seamless feedback loop.

The agent consumes unstructured business requirements, opens a browser, identifies elements using AI vision + DOM analysis, executes test steps with self-healing locator fallback, and generates documentation and automation scripts automatically.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS TEST AGENT                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐  │
│  │ Requirement  │───>│  AI Engine    │───>│ Locator Engine │  │
│  │ Parser       │    │ (Gemini/     │    │ (Ranked        │  │
│  │ (.docx/xlsx) │    │  Claude)     │    │  Locators)     │  │
│  └─────────────┘    └──────────────┘    └───────┬────────┘  │
│                           │                      │           │
│  ┌─────────────┐          │              ┌───────▼────────┐  │
│  │ RAG Engine   │─────────┘              │ Action         │  │
│  │ (Knowledge   │                        │ Executor       │  │
│  │  Base)       │                        │ (Self-Healing) │  │
│  └─────────────┘                         └───────┬────────┘  │
│                                                  │           │
│  ┌──────────────────────────────────────────────▼────────┐  │
│  │              PARALLEL ARTIFACT GENERATION              │  │
│  ├──────────────┬────────────────┬───────────────────────┤  │
│  │ Playwright   │ Word Test Case │ HTML/JSON Execution   │  │
│  │ Script (.py) │ Document(.docx)│ Report                │  │
│  └──────────────┴────────────────┴───────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Features

- **AI-Driven Element ID** — Screenshot + DOM sent to Gemini or Claude for multimodal locator identification
- **Self-Healing Locators** — Primary/secondary/tertiary locator fallback (data-testid > id > ARIA > CSS > XPath > visual)
- **Requirement Parsing** — Extracts intent and expected results from `.docx` and `.xlsx` files
- **RAG Knowledge Base** — Ingests user manuals to augment AI context with domain knowledge
- **Parallel Artifact Generation** — Simultaneously produces Playwright scripts, Word test cases, and HTML reports
- **Multi-Model Support** — Swap between Gemini (speed) and Claude (deep reasoning) via config
- **Rich CLI** — Beautiful terminal output with progress tracking and result tables

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- A valid API key for **Claude** (Anthropic) and/or **Gemini** (Google)

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Configure

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your API keys
# CLAUDE_API_KEY=sk-ant-...
# GEMINI_API_KEY=AIza...
# TARGET_URL=https://your-app.com
```

Review `config/config.yaml` to customize Playwright settings, AI models, and artifact generation.

### 4. Run

```bash
# Full pipeline with a requirement document
python main.py --requirements input/requirements.docx --url https://your-app.com

# Full pipeline with inline text
python main.py --text "Login with valid credentials and verify the dashboard loads" --url https://your-app.com

# With RAG knowledge base
python main.py -r input/requirements.docx -u https://your-app.com -k input/manuals/

# Demo mode (single step)
python main.py --demo --url https://your-app.com --intent "Click the Login button"

# Use Gemini instead of Claude
python main.py -r input/requirements.docx -u https://your-app.com --provider GEMINI

# Run headless
python main.py -r input/requirements.docx -u https://your-app.com --headless
```

---

## Project Structure

```
├── config/
│   └── config.yaml              # AI provider & Playwright configuration
├── core/
│   ├── agent.py                 # Main orchestrator (pipeline controller)
│   ├── ai_engine.py             # Multi-model AI inference (Gemini/Claude)
│   ├── config_loader.py         # YAML + .env configuration loader
│   ├── locator_engine.py        # AI-driven locator identification
│   ├── action_executor.py       # Self-healing action execution
│   ├── requirement_parser.py    # .docx/.xlsx requirement parser
│   └── state_capture.py         # Playwright page state capture
├── generators/
│   ├── script_generator.py      # Python Playwright script generator
│   ├── docx_generator.py        # Word test case document generator
│   └── report_generator.py      # HTML/JSON execution report generator
├── knowledge/
│   └── rag_engine.py            # RAG knowledge base (ChromaDB)
├── models/
│   └── schemas.py               # Pydantic data models
├── utils/
│   ├── dom_utils.py             # DOM minification & extraction
│   └── screenshot_utils.py      # Screenshot processing
├── input/                       # Place requirement docs here
├── output/                      # Generated artifacts appear here
│   ├── scripts/                 # Generated Playwright scripts
│   ├── testcases/               # Generated Word documents
│   ├── reports/                 # HTML/JSON execution reports
│   └── screenshots/             # Step-by-step screenshots
├── main.py                      # CLI entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
└── README.md
```

---

## Self-Healing Flow

```
Step: "Click Login"
  │
  ├─ Try PRIMARY locator (data-testid="login-btn")  ──── Success → PASSED
  │
  ├─ Try SECONDARY locator (aria-label="Login")     ──── Success → HEALED
  │
  ├─ Try TERTIARY locator (//button[text()='Login'])──── Success → HEALED
  │
  └─ All failed                                      ──── FAILED
```

When a step is **healed**, the generated Playwright script includes the working locator as primary and documents the failed ones as comments for future reference.

---

## Generated Artifacts

### 1. Python Playwright Script (`output/scripts/`)
Clean, PEP8-compliant `.py` file with setup, teardown, ranked locators, and backup comments.

### 2. Word Test Case (`output/testcases/`)
Structured `.docx` with:
- Test case metadata table
- Step-by-step execution table (Step #, Action, Data, Expected, Status, Locator)
- Embedded before/after screenshots
- Execution summary

### 3. Execution Report (`output/reports/`)
Modern dark-theme HTML dashboard with:
- Pass/fail/heal statistics
- Step-by-step details with locator info
- AI usage log (provider, tokens, latency, reasoning)
- Also saved as JSON for programmatic access

---

## Configuration Reference

| Setting | YAML Path | Env Variable | Default |
|---|---|---|---|
| AI Provider | `ai_provider` | `AI_PROVIDER` | `CLAUDE` |
| Claude Key | `api_keys.claude` | `CLAUDE_API_KEY` | — |
| Gemini Key | `api_keys.gemini` | `GEMINI_API_KEY` | — |
| Target URL | — | `TARGET_URL` | — |
| Headless | `playwright.headless` | — | `false` |
| Max Retries | `self_healing.max_retries` | — | `3` |
| Output Dir | `artifacts.output_dir` | — | `output` |

See `config/config.yaml` for the full reference.

---

## License

MIT
