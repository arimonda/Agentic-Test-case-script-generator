# Self-Healing Autonomous Test Agent

# User Guide

**Version 1.0 | February 2026**
**Confidential — Internal Use Only**

---

## Table of Contents

- [1. Introduction](#1-introduction)
  - [1.1 What Is This Tool?](#11-what-is-this-tool)
  - [1.2 Who Should Use This Guide?](#12-who-should-use-this-guide)
  - [1.3 Key Capabilities at a Glance](#13-key-capabilities-at-a-glance)
  - [1.4 How It Works — The Big Picture](#14-how-it-works--the-big-picture)
- [2. Installation & Setup](#2-installation--setup)
  - [2.1 System Requirements](#21-system-requirements)
  - [2.2 Step-by-Step Installation](#22-step-by-step-installation)
  - [2.3 Configuring API Keys](#23-configuring-api-keys)
  - [2.4 Verifying Your Installation](#24-verifying-your-installation)
- [3. Configuration](#3-configuration)
  - [3.1 The .env File](#31-the-env-file)
  - [3.2 The config.yaml File](#32-the-configyaml-file)
  - [3.3 Configuration Precedence](#33-configuration-precedence)
  - [3.4 Choosing an AI Provider](#34-choosing-an-ai-provider)
- [4. Preparing Your Test Inputs](#4-preparing-your-test-inputs)
  - [4.1 Supported Input Formats](#41-supported-input-formats)
  - [4.2 Writing Good Requirements (Text)](#42-writing-good-requirements-text)
  - [4.3 Structuring Word Documents (.docx)](#43-structuring-word-documents-docx)
  - [4.4 Structuring Excel Files (.xlsx)](#44-structuring-excel-files-xlsx)
  - [4.5 Using Inline Text](#45-using-inline-text)
  - [4.6 Sample Test Data Included](#46-sample-test-data-included)
- [5. Running Tests](#5-running-tests)
  - [5.1 Full Pipeline Mode](#51-full-pipeline-mode)
  - [5.2 Demo Mode (Single Step)](#52-demo-mode-single-step)
  - [5.3 Using the Knowledge Base (RAG)](#53-using-the-knowledge-base-rag)
  - [5.4 Headless Mode for CI/CD](#54-headless-mode-for-cicd)
  - [5.5 Complete Command Reference](#55-complete-command-reference)
- [6. Understanding the Output](#6-understanding-the-output)
  - [6.1 Console Output](#61-console-output)
  - [6.2 Python Playwright Scripts](#62-python-playwright-scripts)
  - [6.3 Word Test Case Documents](#63-word-test-case-documents)
  - [6.4 HTML Execution Reports](#64-html-execution-reports)
  - [6.5 JSON Reports](#65-json-reports)
  - [6.6 Screenshots](#66-screenshots)
  - [6.7 Output Folder Structure](#67-output-folder-structure)
- [7. Self-Healing — How It Works](#7-self-healing--how-it-works)
  - [7.1 The Problem It Solves](#71-the-problem-it-solves)
  - [7.2 The Three-Tier Locator Strategy](#72-the-three-tier-locator-strategy)
  - [7.3 The Healing Process in Action](#73-the-healing-process-in-action)
  - [7.4 Understanding PASSED vs HEALED vs FAILED](#74-understanding-passed-vs-healed-vs-failed)
- [8. The Knowledge Base (RAG)](#8-the-knowledge-base-rag)
  - [8.1 What Is RAG?](#81-what-is-rag)
  - [8.2 Preparing Knowledge Base Documents](#82-preparing-knowledge-base-documents)
  - [8.3 What Makes a Good Knowledge Base?](#83-what-makes-a-good-knowledge-base)
  - [8.4 How RAG Improves Test Accuracy](#84-how-rag-improves-test-accuracy)
- [9. Working with AI Providers](#9-working-with-ai-providers)
  - [9.1 Google Gemini](#91-google-gemini)
  - [9.2 Anthropic Claude](#92-anthropic-claude)
  - [9.3 When to Use Which Provider](#93-when-to-use-which-provider)
  - [9.4 Understanding Token Usage & Cost](#94-understanding-token-usage--cost)
- [10. Step-by-Step Walkthroughs](#10-step-by-step-walkthroughs)
  - [10.1 Walkthrough A: Login Test](#101-walkthrough-a-login-test)
  - [10.2 Walkthrough B: End-to-End Checkout](#102-walkthrough-b-end-to-end-checkout)
  - [10.3 Walkthrough C: Negative Testing](#103-walkthrough-c-negative-testing)
- [11. Best Practices](#11-best-practices)
- [12. Troubleshooting](#12-troubleshooting)
- [13. Frequently Asked Questions](#13-frequently-asked-questions)
- [14. Glossary](#14-glossary)

---

## 1. Introduction

### 1.1 What Is This Tool?

The **Self-Healing Autonomous Test Agent** is an AI-powered system that transforms plain-English business requirements into fully executed browser tests — without you writing a single line of Playwright code.

You give it a requirement document (or just type a sentence), and it:

1. **Reads** your requirements and understands what to test
2. **Opens** a real Chromium browser
3. **Looks** at each page (screenshot + HTML analysis via AI)
4. **Finds** UI elements using Computer Vision and DOM parsing
5. **Acts** on those elements (click, type, select, verify)
6. **Heals** itself when a locator fails by trying backup strategies
7. **Produces** three artifacts: a Playwright script, a Word test case, and an HTML report

### 1.2 Who Should Use This Guide?

This guide is for:

- **QA Engineers** who want to convert requirements to automated tests quickly
- **Test Managers** who need structured test documentation
- **Business Analysts** who write requirements and want to see them tested
- **Anyone** who wants to automate browser testing without deep coding knowledge

You do **not** need to be a programmer to use this tool. You need:
- Basic command-line skills (running commands in a terminal)
- An API key for Google Gemini or Anthropic Claude
- A web application you want to test

### 1.3 Key Capabilities at a Glance

| Capability | Description |
|---|---|
| **Requirement Parsing** | Reads `.docx`, `.xlsx`, and `.txt` files to extract test steps |
| **AI Vision** | Sends page screenshots to AI to visually identify elements |
| **DOM Analysis** | Parses and minifies HTML to find reliable element selectors |
| **Self-Healing** | 3-tier locator fallback (primary → secondary → tertiary) |
| **Script Generation** | Outputs clean Python Playwright `.py` files |
| **Test Case Docs** | Outputs Word `.docx` with tables, screenshots, and summaries |
| **Execution Reports** | Outputs dark-themed HTML dashboards + machine-readable JSON |
| **Knowledge Base** | RAG system ingests user manuals for smarter element identification |
| **Multi-Model** | Switch between Gemini (fast) and Claude (deep reasoning) |

### 1.4 How It Works — The Big Picture

```
  YOUR REQUIREMENTS                          YOUR OUTPUTS
  ─────────────────                          ────────────
  ┌──────────────┐                           ┌──────────────────┐
  │ requirements │     ┌──────────────┐      │ Playwright Script │
  │ .docx/.xlsx  │────>│              │─────>│ (.py)             │
  │ .txt / text  │     │  AUTONOMOUS  │      ├──────────────────┤
  └──────────────┘     │  TEST AGENT  │      │ Word Test Case   │
                       │              │─────>│ (.docx)           │
  ┌──────────────┐     │  AI + Browser│      ├──────────────────┤
  │ User Manuals │────>│  + Self-Heal │─────>│ HTML Report      │
  │ (RAG)        │     │              │      │ (.html + .json)   │
  └──────────────┘     └──────────────┘      ├──────────────────┤
                                             │ Screenshots      │
                                             │ (before/after)   │
                                             └──────────────────┘
```

---

## 2. Installation & Setup

### 2.1 System Requirements

| Component | Requirement |
|---|---|
| **Operating System** | Windows 10/11, macOS, or Linux |
| **Python** | Version 3.9 or higher |
| **RAM** | 4 GB minimum (8 GB recommended) |
| **Disk Space** | ~500 MB for dependencies + browser |
| **Internet** | Required for AI API calls |
| **API Key** | Google Gemini and/or Anthropic Claude |

### 2.2 Step-by-Step Installation

**Step 1 — Open a terminal** in the project root folder:
```
c:\Users\arimo\.projects\Agentic Test case script generator
```

**Step 2 — Create a Python virtual environment:**
```bash
python -m venv .venv
```

**Step 3 — Activate the virtual environment:**

On **Windows** (PowerShell):
```powershell
.venv\Scripts\activate
```

On **Windows** (Command Prompt):
```cmd
.venv\Scripts\activate.bat
```

On **macOS / Linux**:
```bash
source .venv/bin/activate
```

You should see `(.venv)` appear in your terminal prompt.

**Step 4 — Install Python packages:**
```bash
pip install -r requirements.txt
```

> **Note:** If installation is slow, try: `pip install --timeout 300 -r requirements.txt`

**Step 5 — Install the Playwright browser:**
```bash
playwright install chromium
```

This downloads the Chromium browser binary (~150 MB).

### 2.3 Configuring API Keys

**Step 1 — Create your environment file:**

On Windows:
```powershell
copy .env.example .env
```

On macOS/Linux:
```bash
cp .env.example .env
```

**Step 2 — Edit `.env`** with your text editor and add your API keys:

```env
GEMINI_API_KEY=your_gemini_key_here
CLAUDE_API_KEY=your_claude_key_here
TARGET_URL=https://www.saucedemo.com
AI_PROVIDER=GEMINI
```

You only need **one** of the two API keys. If you only have Gemini, leave `CLAUDE_API_KEY` blank (and vice versa).

> **SECURITY WARNING:** Never share your `.env` file. Never commit it to Git. The `.gitignore` is already configured to exclude it.

### 2.4 Verifying Your Installation

Run the demo mode to verify everything works:

```bash
python main.py --demo --url https://www.saucedemo.com --intent "Verify the login page loads"
```

If successful, you'll see:
- A Chromium browser window open briefly
- Console output showing the step status
- A screenshot saved in `output/screenshots/`

---

## 3. Configuration

### 3.1 The .env File

The `.env` file stores sensitive values (API keys) and quick overrides:

```env
# Required: At least one AI key
GEMINI_API_KEY=AIza...
CLAUDE_API_KEY=sk-ant-...

# Optional
OPENAI_API_KEY=               # For premium RAG embeddings
TARGET_URL=https://your-app.com  # Default target URL
AI_PROVIDER=GEMINI            # Default provider
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR
```

### 3.2 The config.yaml File

The `config/config.yaml` file controls all runtime behavior. Key sections:

**AI Provider & Models:**
```yaml
ai_provider: "GEMINI"          # Which AI to use by default

models:
  gemini:
    vision_model: "gemini-2.5-flash"
    text_model: "gemini-2.5-flash"
    max_tokens: 4096
    temperature: 0.2           # Lower = more deterministic
  claude:
    vision_model: "claude-sonnet-4-20250514"
    text_model: "claude-sonnet-4-20250514"
```

**Playwright Browser:**
```yaml
playwright:
  headless: false              # Set true for no browser window
  browser: "chromium"          # chromium, firefox, webkit
  viewport:
    width: 1920
    height: 1080
  timeout: 30000               # Action timeout in milliseconds
  navigation_timeout: 60000    # Page load timeout
  retries: 3                   # Self-healing retry count
  slow_mo: 100                 # Milliseconds between actions
```

**Artifact Generation:**
```yaml
artifacts:
  output_dir: "output"
  generate_script: true        # Generate .py files?
  generate_docx: true          # Generate .docx files?
  generate_report: true        # Generate HTML reports?
  screenshot_in_docx: true     # Embed screenshots in Word?
  report_format: "html"        # html or json
```

**Self-Healing:**
```yaml
self_healing:
  enabled: true
  max_retries: 3               # Max locator fallback attempts
  locator_strategies:
    - "test_id"                # data-testid attributes
    - "id"                     # HTML id
    - "aria"                   # ARIA labels/roles
    - "css"                    # CSS selectors
    - "xpath"                  # XPath expressions
    - "visual"                 # Visual text matching
```

**Knowledge Base:**
```yaml
rag:
  enabled: true
  chunk_size: 1000             # Document chunk size in characters
  chunk_overlap: 200           # Overlap between chunks
```

### 3.3 Configuration Precedence

When the same setting is defined in multiple places, this order wins:

```
Command-line flags  >  Environment variables (.env)  >  config.yaml  >  Built-in defaults
```

For example, `--provider CLAUDE` on the command line overrides `AI_PROVIDER=GEMINI` in `.env`, which overrides `ai_provider: "GEMINI"` in `config.yaml`.

### 3.4 Choosing an AI Provider

| Factor | Gemini | Claude |
|---|---|---|
| **Speed** | Fast (1-3 seconds per step) | Moderate (3-8 seconds per step) |
| **Vision Quality** | Excellent (native multimodal) | Excellent (base64 images) |
| **Reasoning** | Good | Excellent |
| **Cost** | Low | Moderate |
| **Best For** | Real-time element ID, high-volume testing | Complex test planning, tricky UIs |

**Recommendation:** Start with **Gemini** for daily testing. Switch to **Claude** when Gemini struggles with complex or ambiguous UI elements.

---

## 4. Preparing Your Test Inputs

### 4.1 Supported Input Formats

| Format | Extension | How It's Parsed |
|---|---|---|
| **Plain Text** | `.txt` | Read as-is, sent to AI for structuring |
| **Word Document** | `.docx` | Paragraphs + table cells extracted |
| **Excel Spreadsheet** | `.xlsx` | All sheets read with headers as context |
| **Inline Text** | (command line) | Passed directly via `--text` flag |

### 4.2 Writing Good Requirements (Text)

The AI works best when your requirements are clear and specific. Here's the ideal format:

```
Test Requirement: Valid User Login

Application URL: https://www.saucedemo.com

Objective: Verify that a standard user can log in successfully.

Steps:
1. Navigate to https://www.saucedemo.com
2. Enter "standard_user" into the Username field
3. Enter "secret_sauce" into the Password field
4. Click the "Login" button
5. Verify the Products page is displayed with product items visible

Expected Outcome: User sees the product inventory page.

Test Data:
  Username: standard_user
  Password: secret_sauce
```

**Tips for best results:**
- State the URL explicitly
- Use verbs like "Click", "Enter", "Type", "Select", "Verify"
- Include the exact data to enter
- Describe what success looks like for each step
- Give elements their visible labels (e.g., "the Login button", "the Username field")

### 4.3 Structuring Word Documents (.docx)

For Word documents, use this structure:

1. **Heading** — Test case name and description
2. **Paragraph** — Objective and preconditions
3. **Table** — Steps with columns:

| Step | Action | Input Data | Expected Result |
|---|---|---|---|
| 1 | Navigate to the application URL | https://www.saucedemo.com | Login page displayed |
| 2 | Enter the username | standard_user | Username field populated |
| 3 | Enter the password | secret_sauce | Password field masked |
| 4 | Click the Login button | | Products page loads |

The parser reads both paragraph text AND table cells, so include context in both.

### 4.4 Structuring Excel Files (.xlsx)

For Excel files, use columns like:

| Test ID | Scenario | Step | Action | Input Data | Expected Result | Priority |
|---|---|---|---|---|---|---|
| TC-001 | Valid Login | 1 | Navigate to saucedemo.com | https://www.saucedemo.com | Login page loads | High |
| TC-001 | Valid Login | 2 | Enter username | standard_user | Username entered | High |

Each sheet can contain different test scenarios. The parser reads all sheets.

### 4.5 Using Inline Text

For quick one-off tests, skip the file entirely:

```bash
python main.py --text "Login as standard_user with password secret_sauce and verify the Products page loads with 6 items" --url https://www.saucedemo.com
```

### 4.6 Sample Test Data Included

The project comes with ready-to-use sample test data in `input/`:

```
input/
├── requirements/
│   ├── TC001_valid_login.txt              # 9-step login test
│   ├── TC002_invalid_login_scenarios.txt   # 5 negative login scenarios
│   ├── TC003_product_browsing.txt          # Product catalog + sorting
│   ├── TC004_cart_management.txt           # Cart add/remove/multi-item
│   ├── TC005_checkout_complete_flow.txt    # Full E2E checkout (34 steps)
│   ├── TC006_checkout_validation.txt       # Form validation tests
│   ├── TC007_sidebar_navigation.txt        # Menu, logout, reset
│   └── TC008_edge_cases_and_performance.txt # Special users, edge cases
├── manuals/
│   ├── saucedemo_app_manual.txt           # Complete app reference (RAG)
│   └── saucedemo_test_credentials.txt     # All test data reference
└── sample_data/
    └── test_suite_full.json               # Full JSON test suite
```

All samples target **SauceDemo** (https://www.saucedemo.com), a free demo e-commerce site.

---

## 5. Running Tests

### 5.1 Full Pipeline Mode

The standard way to run a test:

```bash
python main.py --requirements input/requirements/TC001_valid_login.txt --url https://www.saucedemo.com
```

**What happens step by step:**

1. **Config loaded** — reads `.env` and `config.yaml`
2. **Requirements parsed** — AI reads your document and extracts structured test steps
3. **Browser opens** — Chromium launches with the configured viewport (1920x1080)
4. **Navigates** — goes to the target URL
5. **For each test step:**
   - Takes a full-page screenshot
   - Captures and minifies the page HTML
   - Sends screenshot + HTML to the AI with the step intent
   - AI returns 3 ranked locators (primary/secondary/tertiary)
   - Executes the action (click, fill, etc.) with self-healing fallback
   - Captures before/after screenshots
6. **Artifacts generated** — Script, Word doc, and HTML report created in parallel
7. **Results displayed** — Rich table in the console

### 5.2 Demo Mode (Single Step)

Demo mode executes just one action — useful for testing your setup:

```bash
python main.py --demo --url https://www.saucedemo.com --intent "Click the Login button"
```

Output:
```
Demo Mode: Executing single step: 'Click the Login button'

  Status: passed
  Locator: LocatorSet(element_name='Login Button', ...)
  Duration: 2847 ms
```

### 5.3 Using the Knowledge Base (RAG)

Feed user manuals to improve AI accuracy:

```bash
python main.py -r input/requirements/TC005_checkout_complete_flow.txt \
  -u https://www.saucedemo.com \
  -k input/manuals/
```

The `-k` flag points to a directory containing `.docx`, `.txt`, or `.md` files. These are chunked, embedded, and stored in a local vector database. For each test step, the 3 most relevant chunks are retrieved and included in the AI prompt.

### 5.4 Headless Mode for CI/CD

Run without a visible browser window:

```bash
python main.py -r input/requirements/TC001_valid_login.txt \
  -u https://www.saucedemo.com \
  --headless
```

For CI/CD pipelines, parse the JSON report:
```bash
# Run the test
python main.py -r requirements.txt -u https://staging.app.com --headless

# Check results (the JSON report is in output/reports/)
```

### 5.5 Complete Command Reference

```
python main.py [OPTIONS]

INPUT (one required):
  -r, --requirements PATH     Path to .docx, .xlsx, or .txt requirement file
  -t, --text TEXT              Inline requirement text
  --demo                       Demo mode (single step, requires --intent)

REQUIRED:
  -u, --url URL               Target application URL

OPTIONAL:
  -k, --knowledge DIR         Directory with documents for RAG knowledge base
  -c, --config PATH           Config YAML path (default: config/config.yaml)
  --intent TEXT               Action intent for demo mode
  --provider {GEMINI,CLAUDE}  Override AI provider for this run
  --headless                  Run without visible browser window
  --log-level {DEBUG,INFO,WARNING,ERROR}  Logging verbosity
```

**Common commands:**

```bash
# Basic test with a file
python main.py -r input/requirements/TC001_valid_login.txt -u https://www.saucedemo.com

# Inline quick test
python main.py -t "Login and verify products page" -u https://www.saucedemo.com

# Full E2E with knowledge base and Gemini
python main.py -r input/requirements/TC005_checkout_complete_flow.txt \
  -u https://www.saucedemo.com -k input/manuals/ --provider GEMINI

# Headless with Claude and debug logging
python main.py -r input/requirements/TC001_valid_login.txt \
  -u https://www.saucedemo.com --headless --provider CLAUDE --log-level DEBUG

# Demo mode
python main.py --demo -u https://www.saucedemo.com --intent "Click the Login button"
```

---

## 6. Understanding the Output

### 6.1 Console Output

When a test completes, you'll see a rich table in the terminal:

```
┌───────────────────────────────────────────────────────────────┐
│ Results: Valid User Login                                     │
├──────┬──────────────────────────────────┬────────┬────────┬──┤
│ Step │ Intent                           │ Status │ Healed │  │
├──────┼──────────────────────────────────┼────────┼────────┼──┤
│ 1    │ Navigate to the application URL  │ PASSED │ 0      │  │
│ 2    │ Enter the username               │ PASSED │ 0      │  │
│ 3    │ Enter the password               │ HEALED │ 1      │  │
│ 4    │ Click the Login button           │ PASSED │ 0      │  │
│ 5    │ Verify products page loaded      │ PASSED │ 0      │  │
└──────┴──────────────────────────────────┴────────┴────────┴──┘

  Overall: HEALED  |  Passed: 4  |  Failed: 0  |  Healed: 1  |  Duration: 12340 ms
```

**Color coding:**
- **Green (PASSED)** — Step succeeded with the primary locator
- **Yellow (HEALED)** — Step succeeded with a backup locator
- **Red (FAILED)** — Step failed even after trying all locators

### 6.2 Python Playwright Scripts

Location: `output/scripts/test_<name>.py`

Generated scripts are:
- **Runnable** — execute directly with `python output/scripts/test_valid_login.py`
- **PEP8 compliant** — clean, readable Python code
- **Documented** — every step has comments with intent and expected result
- **Self-healing aware** — backup locators included as comments

Example excerpt:
```python
# Step 2: Enter the username
# Expected: Username field displays "standard_user"
# Element: Username Input
page.locator("#user-name").fill("standard_user")
# --- Backup locators (self-healing) ---
# Backup 2 (aria): page.get_by_label("Username")
# Backup 3 (css): page.locator("input[data-test='username']")
```

### 6.3 Word Test Case Documents

Location: `output/testcases/TC_<name>_<timestamp>.docx`

Contains:
- **Title page** with test case name and generation timestamp
- **Metadata table** — ID, description, preconditions, URL, source file, step count, overall status
- **Steps table** — 6 columns: Step #, Action, Input Data, Expected Result, Status, Locator
  - Status cells are color-coded (green/red/yellow)
- **Screenshots section** — Before and after screenshots for every step
- **Summary section** — Pass/fail/heal counts, duration, healing attempts

### 6.4 HTML Execution Reports

Location: `output/reports/report_<name>_<timestamp>.html`

A modern dark-themed dashboard featuring:

- **Statistics cards** — Total steps, passed, failed, healed, duration, AI tokens used
- **Step-by-step cards** — Each step with:
  - Action type and input data
  - Expected vs actual result
  - Status badge (color-coded)
  - Primary locator with confidence score
  - Error details (if failed)
- **AI Usage table** — For each step: provider, tokens consumed, latency, reasoning

Open in any browser to view.

### 6.5 JSON Reports

Location: `output/reports/report_<name>_<timestamp>.json`

Machine-readable version of the HTML report. Contains:
- Full test case definition
- All step results with locators and timing
- Summary statistics
- AI usage log

Ideal for CI/CD pipeline integration.

### 6.6 Screenshots

Location: `output/screenshots/`

For each step:
- `step1_before.png` — What the page looked like before the action
- `step1_after.png` — What the page looked like after the action
- Timestamped page-state captures for AI analysis

### 6.7 Output Folder Structure

```
output/
├── scripts/                    # Generated Playwright .py files
│   └── test_valid_user_login.py
├── testcases/                  # Generated Word .docx documents
│   └── TC_Valid_User_Login_20260216_120000.docx
├── reports/                    # HTML + JSON execution reports
│   ├── report_Valid_User_Login_20260216_120000.html
│   └── report_Valid_User_Login_20260216_120000.json
├── screenshots/                # Before/after screenshots per step
│   ├── step_1_20260216_120001.png
│   ├── step1_before.png
│   ├── step1_after.png
│   └── ...
└── vectorstore/                # RAG knowledge base (if used)
    └── (ChromaDB files)
```

---

## 7. Self-Healing — How It Works

### 7.1 The Problem It Solves

Traditional automated tests break when developers make even small UI changes:
- Rename `id="login-btn"` to `id="submit-login"` → **all tests using that ID fail**
- Change a CSS class → tests using that class fail
- Restructure HTML → XPath selectors break

This means someone must manually update test scripts every time the UI changes. Self-healing eliminates most of this maintenance.

### 7.2 The Three-Tier Locator Strategy

For every UI element, the AI identifies **three** locators ranked by reliability:

| Tier | Strategy | Example | When It Works |
|---|---|---|---|
| **PRIMARY** | `data-testid` or `id` | `page.locator("#login-button")` | Best — survives most UI changes |
| **SECONDARY** | ARIA label or CSS | `page.get_by_label("Login")` | Good — survives HTML restructuring |
| **TERTIARY** | XPath or visual text | `page.get_by_text("Login")` | Fallback — works even when IDs change |

The AI decides which strategy is primary based on what's available in the HTML and how reliable each option is. It assigns a **confidence score** (0.0 to 1.0) to each locator.

### 7.3 The Healing Process in Action

When the agent executes a step like "Click the Login button":

```
Step: Click the Login button
│
├─ TRY PRIMARY: page.locator("#login-button")
│   ├─ Element found? YES → Click it → STATUS: PASSED ✓
│   └─ Element not found or timeout?
│       │
│       ├─ TRY SECONDARY: page.get_by_role("button", name="Login")
│       │   ├─ Found? YES → Click it → STATUS: HEALED ✓
│       │   └─ Not found?
│       │       │
│       │       ├─ TRY TERTIARY: page.get_by_text("Login")
│       │       │   ├─ Found? YES → Click it → STATUS: HEALED ✓
│       │       │   └─ Not found → STATUS: FAILED ✗
```

### 7.4 Understanding PASSED vs HEALED vs FAILED

| Status | Meaning | Action Needed |
|---|---|---|
| **PASSED** | Primary locator worked | None — everything is fine |
| **HEALED** | Primary failed, but a backup worked | Review the generated script — the working locator is used as primary, failed ones as comments |
| **FAILED** | All 3 locators failed | Manual investigation needed — check screenshots in `output/screenshots/` |

A test case's overall status is:
- **PASSED** if all steps passed
- **HEALED** if any step was healed (but none failed)
- **FAILED** if any step failed

---

## 8. The Knowledge Base (RAG)

### 8.1 What Is RAG?

RAG stands for **Retrieval Augmented Generation**. It means: before asking the AI to identify an element, we first search a knowledge base for relevant information and include it in the prompt.

For example, if the test step says "Navigate to the checkout page," and your user manual says "The checkout button (id: checkout) is on the cart page (URL: /cart.html)," the AI gets this context and produces better locators.

### 8.2 Preparing Knowledge Base Documents

Place your documents in `input/manuals/`:

```
input/manuals/
├── app_user_manual.docx       # Application user manual
├── technical_reference.txt    # Technical element reference
└── navigation_guide.md        # How to navigate the app
```

Supported formats: `.docx`, `.txt`, `.md`

### 8.3 What Makes a Good Knowledge Base?

Include documents that describe:

- **Page layouts** — What elements are on each page
- **Element IDs and selectors** — `id`, `class`, `data-testid` attributes
- **Navigation paths** — How to get from page A to page B
- **Form fields** — What inputs exist and their validation rules
- **Error messages** — Expected error text for negative scenarios
- **Business terminology** — Domain-specific names for UI elements

The sample `input/manuals/saucedemo_app_manual.txt` is an excellent example — it lists every page, every element with its selector, and all navigation flows.

### 8.4 How RAG Improves Test Accuracy

| Without RAG | With RAG |
|---|---|
| AI guesses element selectors from screenshot alone | AI knows exact IDs from the manual |
| May use fragile XPath locators | Uses stable `data-testid` or `id` selectors |
| Can miss hidden or off-screen elements | Knows elements exist from documentation |
| Generic locator descriptions | Precise, application-specific locators |

---

## 9. Working with AI Providers

### 9.1 Google Gemini

- **Model:** `gemini-2.5-flash`
- **Strength:** Speed and native multimodal (image + text in one call)
- **Cost:** Low (~$0.01-0.05 per test run)
- **Best for:** Daily testing, high volume, real-time element identification

### 9.2 Anthropic Claude

- **Model:** `claude-sonnet-4-20250514`
- **Strength:** Deep reasoning, complex planning, nuanced understanding
- **Cost:** Moderate (~$0.10-0.30 per test run)
- **Best for:** Complex UIs, generating the initial test plan, tricky locator scenarios

### 9.3 When to Use Which Provider

| Scenario | Recommended Provider |
|---|---|
| Quick smoke tests | Gemini |
| Full regression suite | Gemini |
| Complex multi-step checkout flows | Claude |
| UI with many similar elements | Claude |
| Budget-conscious testing | Gemini |
| When Gemini returns bad locators | Try Claude |

### 9.4 Understanding Token Usage & Cost

Each test step consumes approximately:

| Component | Tokens |
|---|---|
| Minified HTML sent to AI | 500 — 2,000 |
| Locator identification prompt | ~800 |
| Screenshot (image tokens) | ~1,000 — 2,000 |
| AI response (locators JSON) | ~300 — 500 |
| **Total per step** | **~2,600 — 5,300** |

For a 10-step test: ~26,000 — 53,000 tokens total.

The HTML report includes an **AI Usage** table showing exact token counts per step.

---

## 10. Step-by-Step Walkthroughs

### 10.1 Walkthrough A: Login Test

**Goal:** Test that `standard_user` can log in to SauceDemo.

**Step 1 — Run the command:**
```bash
python main.py -r input/requirements/TC001_valid_login.txt -u https://www.saucedemo.com
```

**Step 2 — Watch the browser:**
The Chromium browser opens, navigates to SauceDemo, fills in credentials, clicks Login, and lands on the Products page.

**Step 3 — Review console output:**
A table shows each step with PASSED/HEALED/FAILED status.

**Step 4 — Check generated artifacts in `output/`:**
- Open `output/reports/*.html` in a browser for the visual dashboard
- Open `output/testcases/*.docx` in Word for the formal test case
- Review `output/scripts/*.py` for the reusable Playwright script

### 10.2 Walkthrough B: End-to-End Checkout

**Goal:** Full checkout flow from login to order confirmation.

```bash
python main.py -r input/requirements/TC005_checkout_complete_flow.txt \
  -u https://www.saucedemo.com \
  -k input/manuals/
```

This test has 34 steps. The knowledge base (`-k`) helps the AI identify checkout form fields by their exact IDs.

### 10.3 Walkthrough C: Negative Testing

**Goal:** Verify error messages for invalid logins.

```bash
python main.py -r input/requirements/TC002_invalid_login_scenarios.txt \
  -u https://www.saucedemo.com
```

The AI parses all 5 negative scenarios from the document and executes them sequentially.

---

## 11. Best Practices

1. **Start small** — Test with TC001 (login) first to validate your setup
2. **Use the knowledge base** — Always provide manuals for complex applications
3. **Write specific requirements** — "Click the blue Login button" is better than "Log in"
4. **Include test data** — Specify exact usernames, passwords, and form values
5. **Check screenshots on failure** — The `output/screenshots/` folder shows exactly what the browser saw
6. **Use Gemini for speed** — Switch to Claude only when Gemini struggles
7. **Run headless in CI/CD** — Use `--headless` for pipeline integration
8. **Review generated scripts** — Edit them to add custom assertions or waits
9. **Keep requirements atomic** — One file per test scenario works best
10. **Rotate API keys** — Change your keys periodically for security

---

## 12. Troubleshooting

### Error: "No API keys configured"
**Cause:** The `.env` file is missing or has empty API key values.
**Fix:** Create `.env` from `.env.example` and add at least one API key (GEMINI_API_KEY or CLAUDE_API_KEY).

### Error: "No target URL specified"
**Cause:** No `--url` flag and no `TARGET_URL` in `.env`.
**Fix:** Add `--url https://your-app.com` to your command, or set `TARGET_URL` in `.env`.

### Browser doesn't open
**Cause:** Playwright browsers not installed.
**Fix:** Run `playwright install chromium`.

### "Module not found" errors
**Cause:** Virtual environment not activated or packages not installed.
**Fix:** Run `.venv\Scripts\activate` then `pip install -r requirements.txt`.

### AI returns bad or garbled locators
**Cause:** The AI model is confused by the page complexity.
**Fix:**
- Add a knowledge base with element IDs: `-k input/manuals/`
- Try a different provider: `--provider CLAUDE`
- Increase response size: set `max_tokens: 8192` in `config.yaml`

### Steps keep failing even after self-healing
**Cause:** The target element doesn't exist, or the page hasn't finished loading.
**Fix:**
- Check `output/screenshots/` — look at `step<N>_before.png` to see the actual page state
- Increase timeout: set `playwright.timeout: 60000` in `config.yaml`
- Verify the URL is correct and the app is running

### Test is very slow
**Cause:** AI API latency or slow target application.
**Fix:**
- Switch to Gemini (`--provider GEMINI`) — faster than Claude
- Use headless mode (`--headless`) — slightly faster rendering
- Reduce `playwright.slow_mo` to `0` in `config.yaml`
- Close unnecessary browser tabs on your machine

### "Permission denied" or path errors on Windows
**Cause:** Paths with spaces in the project directory name.
**Fix:** Ensure you're running from the correct directory with the virtual environment activated.

---

## 13. Frequently Asked Questions

**Q: Do I need both Gemini and Claude API keys?**
A: No. You only need one. If you have a Gemini key, set `AI_PROVIDER=GEMINI` in `.env`. Leave the other key blank.

**Q: Can I use both providers in the same test run?**
A: Currently, each run uses one provider. Run the same test twice with different `--provider` flags to compare results.

**Q: Does the agent modify my application?**
A: No. It only reads the page (screenshots + DOM) and performs UI interactions (click, type, select). It never changes your backend, database, or source code.

**Q: Can I edit the generated Playwright scripts?**
A: Absolutely. The scripts are designed to be clean and editable. Use them as a starting point and customize with your own assertions, waits, or data-driven logic.

**Q: How much does each test run cost?**
A: With Gemini, a 10-step test costs roughly $0.01-0.05. With Claude, roughly $0.10-0.30. The HTML report shows exact token usage per step.

**Q: Can I run tests in a CI/CD pipeline?**
A: Yes. Use `--headless` mode and parse the JSON report (`output/reports/*.json`) for pass/fail status.

**Q: What browsers are supported?**
A: Chromium (default), Firefox, and WebKit. Change in `config.yaml` under `playwright.browser`. Install with `playwright install firefox` or `playwright install webkit`.

**Q: Does RAG require an OpenAI key?**
A: No. ChromaDB uses its own built-in embedding model. The OpenAI key is only needed if you want to use premium `text-embedding-3-small` embeddings (optional).

**Q: How large can my requirement document be?**
A: The parser automatically chunks long documents into ~8,000-character segments. Very large documents (100+ pages) work but take longer to parse.

**Q: Can I test mobile layouts?**
A: Yes. Change the viewport in `config.yaml`:
```yaml
playwright:
  viewport:
    width: 375
    height: 812
```
This simulates an iPhone X screen.

---

## 14. Glossary

| Term | Definition |
|---|---|
| **Agent** | The autonomous test system that reads requirements and executes browser tests |
| **Artifact** | A generated output file (script, Word doc, or HTML report) |
| **ChromaDB** | A local vector database used for the RAG knowledge base |
| **DOM** | Document Object Model — the HTML structure of a web page |
| **Gemini** | Google's AI model used for fast multimodal analysis |
| **Claude** | Anthropic's AI model used for deep reasoning |
| **Healed** | A test step where the primary locator failed but a backup succeeded |
| **Intent** | What the test step wants to do (e.g., "Click the Login button") |
| **Locator** | A way to find a UI element (e.g., `#login-button`, `aria-label="Login"`) |
| **LocatorSet** | A ranked set of 3 locators: primary, secondary, tertiary |
| **Minified HTML** | HTML with scripts, styles, and non-essential attributes stripped out |
| **Playwright** | Microsoft's browser automation framework used for test execution |
| **RAG** | Retrieval Augmented Generation — using a knowledge base to enhance AI prompts |
| **Self-Healing** | Automatic locator fallback when the primary selector fails |
| **Token** | The unit of text processing used by AI models (roughly 4 characters) |
| **Viewport** | The visible area of the browser window (width x height) |

---

*End of User Guide — Version 1.0*
