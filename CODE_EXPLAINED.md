# Code Explained — Line by Line

## A Plain-Language Guide for Everyone

**Who is this for?** Anyone — even if you've never written code before. This document walks through every single file in the project and explains what each line does using everyday language and simple analogies.

**What does this project do?** Imagine you hire a robot assistant to test a website for you. You hand it a piece of paper that says "Go to this website, type in a username, click the Login button, and check if it worked." The robot opens a real web browser, looks at the screen (using AI eyes), finds the right buttons and fields, clicks them, and then writes you three reports: a script that can repeat the test, a Word document describing what happened, and a beautiful HTML dashboard.

If a button moves or gets renamed, the robot doesn't panic — it has backup plans to find the button using alternative methods. That's the "self-healing" part.

---

## Table of Contents

1. [The Big Picture — How the Whole Thing Works](#1-the-big-picture)
2. [File: main.py — The Front Door](#2-mainpy--the-front-door)
3. [File: config/config.yaml — The Settings File](#3-configconfigyaml--the-settings-file)
4. [File: core/config_loader.py — The Settings Reader](#4-coreconfig_loaderpy--the-settings-reader)
5. [File: models/schemas.py — The Blueprints](#5-modelsschemaspythe-blueprints)
6. [File: core/agent.py — The Boss / Manager](#6-coreagentpy--the-boss)
7. [File: core/ai_engine.py — The AI Brain](#7-coreai_enginepy--the-ai-brain)
8. [File: core/locator_engine.py — The Element Finder](#8-corelocator_enginepy--the-element-finder)
9. [File: core/action_executor.py — The Hands That Click](#9-coreaction_executorpy--the-hands-that-click)
10. [File: core/state_capture.py — The Camera](#10-corestate_capturepy--the-camera)
11. [File: core/requirement_parser.py — The Document Reader](#11-corerequirement_parserpy--the-document-reader)
12. [File: generators/script_generator.py — The Script Writer](#12-generatorsscript_generatorpy--the-script-writer)
13. [File: generators/docx_generator.py — The Report Writer (Word)](#13-generatorsdocx_generatorpy--the-word-report-writer)
14. [File: generators/report_generator.py — The Dashboard Builder](#14-generatorsreport_generatorpy--the-dashboard-builder)
15. [File: knowledge/rag_engine.py — The Memory / Library](#15-knowledgerag_enginepy--the-memory)
16. [File: utils/dom_utils.py — The HTML Cleaner](#16-utilsdom_utilspy--the-html-cleaner)
17. [File: utils/screenshot_utils.py — The Photo Editor](#17-utilsscreenshot_utilspy--the-photo-editor)
18. [File: requirements.txt — The Shopping List](#18-requirementstxt--the-shopping-list)

---

# 1. The Big Picture

Think of the whole system as a **team of specialists** working together:

```
YOU (give instructions)
  │
  ▼
THE BOSS (agent.py) — Manages everything, delegates tasks
  │
  ├──> THE DOCUMENT READER (requirement_parser.py)
  │       "Reads your Word/Excel/text file and understands what to test"
  │
  ├──> THE CAMERA (state_capture.py)
  │       "Takes a photo of the website and reads the page code"
  │
  ├──> THE ELEMENT FINDER (locator_engine.py)
  │       "Shows the photo to AI and asks: Where is the Login button?"
  │
  ├──> THE AI BRAIN (ai_engine.py)
  │       "Talks to Google Gemini or Anthropic Claude — the actual AI"
  │
  ├──> THE HANDS (action_executor.py)
  │       "Actually clicks buttons, types text, checks results"
  │       "If the first method fails, tries backup methods (self-healing)"
  │
  └──> THREE REPORT WRITERS (generators/)
          ├── Script Writer    → Creates a Python file you can rerun
          ├── Word Writer      → Creates a formal .docx document
          └── Dashboard Builder → Creates a beautiful HTML report
```

**Supporting helpers:**
- **The Blueprints** (schemas.py) — Define the shape of all data
- **The Settings** (config.yaml + config_loader.py) — Store your preferences
- **The HTML Cleaner** (dom_utils.py) — Cleans up messy website code
- **The Photo Editor** (screenshot_utils.py) — Resizes screenshots for the AI
- **The Memory** (rag_engine.py) — Remembers info from user manuals

---

# 2. `main.py` — The Front Door

**Analogy:** This is the **reception desk** of the operation. When you type a command in your terminal, this is the first file that runs. It collects your instructions, sets everything up, and starts the process.

```python
"""
Self-Healing Autonomous Test Agent — Entry Point.
```
> **Lines 1-16:** This is a comment block (the text between `"""` marks). It's like a sticky note on the front of a folder explaining what this file does and showing example commands you can type. Python ignores these lines — they're only for humans to read.

```python
import argparse
import asyncio
import logging
import sys
from pathlib import Path
```
> **Lines 18-22:** These are **imports** — think of them as the receptionist pulling tools out of a drawer before starting work.
> - `argparse` — A tool for reading command-line flags (like `--url` and `--requirements`)
> - `asyncio` — A tool that lets the program do things one after another in an orderly way (needed because web browsers are slow and we have to wait for pages to load)
> - `logging` — A tool for printing status messages (like "Step 3 passed!" or "Warning: something went wrong")
> - `sys` — A tool for interacting with the operating system (like exiting the program)
> - `Path` — A tool for working with file paths (like `C:\Users\Documents\file.txt`)

```python
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
```
> **Lines 24-27:** More imports, this time from a library called **Rich**. Rich makes terminal output pretty — colored text, boxes, tables with borders. Without Rich, you'd just see plain white text. With Rich, you get beautiful formatted output.

```python
from core.agent import AutonomousTestAgent
from core.config_loader import load_config
```
> **Lines 29-30:** Importing our own code — the Boss (`AutonomousTestAgent`) and the Settings Reader (`load_config`). This is like saying "I'll need the project manager and the settings file for today's work."

```python
console = Console()
```
> **Line 32:** Create a Console object. Think of this as turning on the printer/display that will show all our colorful output.

---

### The `setup_logging` Function (Lines 35-42)

```python
def setup_logging(level: str = "INFO") -> None:
```
> **Line 35:** We're defining a **function** — a reusable recipe. This one is called `setup_logging`. It takes one input: `level` (a word like "INFO" or "DEBUG" that controls how chatty the program is). `-> None` means this function doesn't give anything back — it just configures things.

```python
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )
```
> **Lines 37-42:** This configures the program's "diary" (the logging system).
> - `level=` — How detailed should the diary be? "DEBUG" records everything (very chatty). "INFO" records important things. "ERROR" only records problems.
> - `format="%(message)s"` — Just show the message, nothing extra.
> - `datefmt="[%X]"` — Show the time in `[HH:MM:SS]` format.
> - `handlers=[RichHandler(...)]` — Use the Rich library to make log messages colorful. `rich_tracebacks=True` means if something crashes, show a nicely formatted error.

---

### The `parse_args` Function (Lines 45-108)

```python
def parse_args() -> argparse.Namespace:
```
> **Line 45:** Another function. This one reads the command-line flags you type. Like when you type `python main.py --url https://example.com --requirements myfile.docx`, this function figures out that `url` is `https://example.com` and `requirements` is `myfile.docx`.

```python
    parser = argparse.ArgumentParser(
        description="Self-Healing Autonomous Test Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
```
> **Lines 47-51:** Create an argument parser — a tool that reads command-line inputs. The `description` is what shows when someone asks for help (`python main.py --help`). The `epilog=__doc__` puts the comment from the top of the file at the bottom of the help text.

```python
    parser.add_argument(
        "--requirements", "-r",
        type=str,
        help="Path to requirement document (.docx or .xlsx)",
    )
```
> **Lines 53-57:** Register a flag called `--requirements` (short version: `-r`). This tells the program where your requirement file is. `type=str` means it expects text (a file path). The `help` text shows up when someone types `python main.py --help`.

> **Lines 58-106:** Similar blocks for all the other flags:
> - `--text` / `-t` — Type a requirement directly instead of giving a file
> - `--url` / `-u` — The website address to test
> - `--knowledge` / `-k` — Folder containing user manuals (for the memory system)
> - `--config` / `-c` — Path to the settings file (defaults to `config/config.yaml`)
> - `--demo` — Run in demo mode (just execute one single action)
> - `--intent` — What action to do in demo mode (e.g., "Click the Login button")
> - `--provider` — Which AI to use: "GEMINI" or "CLAUDE"
> - `--headless` — Run the browser invisibly (no window pops up)
> - `--log-level` — How chatty the program should be

```python
    return parser.parse_args()
```
> **Line 108:** Actually read the command line and return all the values.

---

### The `display_banner` Function (Lines 111-119)

```python
def display_banner() -> None:
    banner = Panel(
        "[bold cyan]Self-Healing Autonomous Test Agent[/bold cyan]\n"
        "[dim]AI-Powered Browser Testing with Computer Vision & Self-Healing Locators[/dim]",
        border_style="bright_blue",
        padding=(1, 2),
    )
    console.print(banner)
```
> **Lines 111-119:** This just shows a pretty welcome box in the terminal when you start the program. `Panel` creates a bordered box. The `[bold cyan]` and `[dim]` are Rich formatting codes (like bold and gray text). Think of it as the program saying "Hello! I'm ready to work!"

---

### The `display_results` Function (Lines 122-167)

```python
def display_results(results) -> None:
```
> **Line 122:** This function takes the test results and displays them as a nice table.

```python
    for result in results:
        tc = result.test_case
        table = Table(
            title=f"Results: {tc.name}",
            show_header=True,
            header_style="bold magenta",
        )
```
> **Lines 124-130:** For each test case result, create a table. The title is the test name. Headers (column titles) are bold magenta (purple).

```python
        table.add_column("Step", style="dim", width=6)
        table.add_column("Intent", width=40)
        table.add_column("Status", width=12)
        table.add_column("Healed", width=8)
        table.add_column("Duration", width=12)
```
> **Lines 131-135:** Define 5 columns: Step number, what the step does (Intent), whether it passed/failed (Status), how many times self-healing kicked in (Healed), and how long it took (Duration).

```python
        for sr in result.step_results:
            status_style = {
                "PASSED": "green",
                "FAILED": "red",
                "HEALED": "yellow",
            }.get(sr.status.value.upper(), "white")
```
> **Lines 137-142:** For each step, pick a color: green for passed, red for failed, yellow for healed (where a backup method was used). If the status doesn't match any of these, use white.

```python
            table.add_row(
                str(sr.step_input.step_number),
                sr.step_input.intent,
                f"[{status_style}]{sr.status.value.upper()}[/{status_style}]",
                str(sr.healing_attempts),
                f"{sr.duration_ms:.0f} ms",
            )
```
> **Lines 144-150:** Add a row to the table with the step number, what the step does, the colored status, how many healing attempts, and the time in milliseconds.

```python
        console.print(table)
```
> **Line 152:** Print the completed table to the screen.

> **Lines 155-167:** Print a summary line below the table showing the overall status, total passed, failed, healed counts, and total time.

---

### The `main` Function (Lines 170-239) — The Heart of It All

```python
async def main() -> None:
```
> **Line 170:** The main function. The `async` keyword means "this function deals with things that take time (like loading web pages) and knows how to wait patiently."

```python
    args = parse_args()
    setup_logging(args.log_level)
    display_banner()
```
> **Lines 172-174:** Step 1: Read command-line flags. Step 2: Set up the diary/logging system. Step 3: Show the welcome banner.

```python
    config = load_config(config_path=args.config)
```
> **Line 177:** Read the settings file (config.yaml + .env). This gives us all our preferences: which AI to use, how big the browser window should be, how many retries to allow, etc.

```python
    if args.url:
        config.target_url = args.url
    if args.provider:
        from models.schemas import AIProvider
        config.ai_provider = AIProvider(args.provider.upper())
    if args.headless:
        config.headless = True
```
> **Lines 179-186:** If you typed `--url`, `--provider`, or `--headless` on the command line, those override whatever was in the settings file. Command-line instructions always win.

```python
    if not config.target_url:
        console.print("[red]Error: No target URL specified. Use --url or set TARGET_URL in .env[/red]")
        sys.exit(1)

    if not config.claude_api_key and not config.gemini_api_key:
        console.print("[red]Error: No API keys configured. Set CLAUDE_API_KEY or GEMINI_API_KEY in .env[/red]")
        sys.exit(1)
```
> **Lines 189-195:** Safety checks. If you forgot to specify a website URL, or forgot to add an AI key, the program shows a red error message and stops. `sys.exit(1)` means "stop the program with an error."

```python
    agent = AutonomousTestAgent(config)
```
> **Line 198:** Create "The Boss" — the main agent that will manage all the work. We hand it our settings so it knows how to behave.

```python
    if args.demo:
        if not args.intent:
            console.print("[red]Error: --intent is required in demo mode[/red]")
            sys.exit(1)

        console.print(f"\n[bold]Demo Mode:[/bold] Executing single step: '{args.intent}'\n")
        result = await agent.run_single_step(
            target_url=config.target_url,
            intent=args.intent,
        )
```
> **Lines 200-210:** If `--demo` was used, run just ONE step. For example: `--demo --intent "Click the Login button"`. The `await` keyword means "start this task and wait for it to finish before continuing." This is necessary because opening a browser and clicking things takes real time.

```python
    else:
        if not args.requirements and not args.text:
            console.print(
                "[red]Error: Provide --requirements or --text[/red]\n"
                "Example: python main.py -r input/requirements.docx -u https://app.example.com"
            )
            sys.exit(1)

        results = await agent.run(
            requirement_file=args.requirements,
            requirement_text=args.text,
            target_url=config.target_url,
            knowledge_dir=args.knowledge,
        )

        display_results(results)
        console.print("[bold green]Artifacts generated in output/ directory[/bold green]")
```
> **Lines 217-235:** If not in demo mode, run the full pipeline. Check that you provided either a file or text. Then tell the Boss to run everything: parse requirements, open browser, execute all steps, generate all reports. Finally, show the results table and tell the user where the output files are.

```python
if __name__ == "__main__":
    asyncio.run(main())
```
> **Lines 238-239:** This is the actual starting point. When you type `python main.py`, Python runs this line first. It says "run the `main()` function using the async system." Think of `asyncio.run()` as pressing the "GO" button.

---

# 3. `config/config.yaml` — The Settings File

**Analogy:** This is like the **preferences page** on your phone. It controls how the whole program behaves. You edit this file to change things without touching any code.

```yaml
# --- AI Provider Selection ---
ai_provider: "GEMINI"
```
> Which AI to use. "GEMINI" is Google's AI (fast and cheap). "CLAUDE" is Anthropic's AI (slower but smarter for complex tasks).

```yaml
api_keys:
  gemini: "${GEMINI_API_KEY}"
  claude: "${CLAUDE_API_KEY}"
```
> Where to find your AI passwords (API keys). The `${...}` means "get this from the .env file." This way the actual secret key isn't stored in this file.

```yaml
models:
  gemini:
    vision_model: "gemini-2.5-flash"
    text_model: "gemini-2.5-flash"
    max_tokens: 4096
    temperature: 0.2
```
> Which specific Gemini model to use. `vision_model` is for when we send screenshots. `text_model` is for text-only questions. `max_tokens: 4096` means "the AI's answer can be at most 4096 words/pieces." `temperature: 0.2` means "be very precise and predictable" (higher = more creative/random).

```yaml
  claude:
    vision_model: "claude-sonnet-4-20250514"
    text_model: "claude-sonnet-4-20250514"
    max_tokens: 4096
    temperature: 0.2
```
> Same settings but for Claude (Anthropic's AI).

```yaml
playwright:
  headless: false
  browser: "chromium"
  screenshot_type: "full_page"
  viewport:
    width: 1920
    height: 1080
  timeout: 30000
  navigation_timeout: 60000
  retries: 3
  slow_mo: 100
```
> Browser settings:
> - `headless: false` — Show the browser window (set to `true` to hide it)
> - `browser: "chromium"` — Use Chrome (can also be "firefox" or "webkit"/Safari)
> - `screenshot_type: "full_page"` — Capture the entire page, even parts you'd need to scroll to see
> - `viewport: width: 1920, height: 1080` — Browser window size (Full HD)
> - `timeout: 30000` — Wait up to 30 seconds (30,000 milliseconds) for an element to appear before giving up
> - `navigation_timeout: 60000` — Wait up to 60 seconds for a page to load
> - `retries: 3` — Try 3 different locators before declaring failure
> - `slow_mo: 100` — Wait 100 milliseconds between actions so you can watch what's happening

```yaml
self_healing:
  enabled: true
  max_retries: 3
  locator_strategies:
    - "test_id"
    - "id"
    - "aria"
    - "css"
    - "xpath"
    - "visual"
```
> Self-healing settings. The list shows the order of methods to find elements:
> 1. `test_id` — Look for a special test attribute (most reliable)
> 2. `id` — Look for the element's unique ID
> 3. `aria` — Look for accessibility labels (for screen readers)
> 4. `css` — Look using CSS styling rules
> 5. `xpath` — Look using the element's position in the page tree
> 6. `visual` — Look for visible text on the screen (last resort)

```yaml
artifacts:
  output_dir: "output"
  generate_script: true
  generate_docx: true
  generate_report: true
  report_format: "html"
```
> What reports to create. All three are turned on (`true`). Files go into the `output/` folder.

```yaml
rag:
  enabled: true
  chunk_size: 1000
  chunk_overlap: 200
```
> Memory system (RAG) settings. `chunk_size: 1000` means break documents into 1000-character pieces. `chunk_overlap: 200` means each piece shares 200 characters with the next piece (so nothing gets lost at the boundaries).

---

# 4. `core/config_loader.py` — The Settings Reader

**Analogy:** This is the **assistant who reads both your settings file and your secret notes (.env file) and combines them into one complete set of instructions.**

```python
import logging
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv
from models.schemas import AIProvider, AppConfig
```
> **Lines 8-15:** Get the tools needed: logging (diary), os (talk to the operating system), Path (handle file paths), yaml (read YAML files), load_dotenv (read .env files), and our own data models.

```python
def load_config(
    config_path: str = "config/config.yaml",
    env_path: str = ".env",
) -> AppConfig:
```
> **Lines 20-23:** Define a function called `load_config`. It takes two file paths (the YAML settings and the .env secrets). It returns an `AppConfig` object (our complete settings).

```python
    env_file = Path(env_path)
    if env_file.exists():
        load_dotenv(env_file)
```
> **Lines 30-32:** Check if the `.env` file exists. If yes, read it and load all the secret values (like API keys) into the system's memory. After this, `os.getenv("GEMINI_API_KEY")` will return your actual key.

```python
    yaml_path = Path(config_path)
    if not yaml_path.exists():
        yaml_config = {}
    else:
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
```
> **Lines 36-42:** Try to open the YAML settings file. If it doesn't exist, use empty settings `{}`. If it does exist, read and parse it. `yaml.safe_load()` converts the human-readable YAML text into a Python dictionary (like a lookup table).

```python
    pw = yaml_config.get("playwright", {})
    models = yaml_config.get("models", {})
    healing = yaml_config.get("self_healing", {})
    artifacts = yaml_config.get("artifacts", {})
    rag = yaml_config.get("rag", {})
```
> **Lines 46-50:** Extract each section of the settings into its own variable. `.get("playwright", {})` means "get the playwright section, or use empty `{}` if it doesn't exist."

```python
    config = AppConfig(
        ai_provider=AIProvider(
            os.getenv("AI_PROVIDER", yaml_config.get("ai_provider", "CLAUDE")).upper()
        ),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        claude_api_key=os.getenv("CLAUDE_API_KEY", ""),
        ...
    )
```
> **Lines 55-98:** Build the final settings object. For each setting, the priority is:
> 1. **First check environment variables** (from .env file) — `os.getenv("GEMINI_API_KEY")`
> 2. **Then check YAML file** — `yaml_config.get("ai_provider")`
> 3. **Finally use a default** — the last value (like `"CLAUDE"` or `""`)
>
> This means you can override any setting by putting it in your .env file, without editing the YAML.

```python
    return config
```
> **Line 101:** Hand back the complete, validated settings object. Every other part of the program will use this.

---

# 5. `models/schemas.py` — The Blueprints

**Analogy:** Before building a house, you need blueprints. Before our program can pass data between its parts, we need to define exactly what that data looks like. This file defines **every type of data** the program uses — like filling out forms that have specific fields.

### Enumerations (Predefined Choices) — Lines 23-59

```python
class LocatorStrategy(str, Enum):
    TEST_ID = "test_id"
    ID = "id"
    ARIA = "aria"
    CSS = "css"
    XPATH = "xpath"
    VISUAL = "visual"
```
> **Lines 23-29:** A **LocatorStrategy** is a list of allowed methods to find an element on a web page. It's like a multiple-choice question: you can ONLY pick one of these 6 options. No other values are allowed. This prevents mistakes.

```python
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
```
> **Lines 32-45:** The 13 types of actions the robot can perform:
> - `click` — Click something
> - `fill` — Type text into a field
> - `select` — Pick from a dropdown menu
> - `check` / `uncheck` — Toggle a checkbox
> - `hover` — Move the mouse over something
> - `navigate` — Go to a web address
> - `wait` — Pause for a moment
> - `assert_visible` — Check that something is visible on screen
> - `assert_text` — Check that specific text appears
> - `assert_value` — Check that a field contains a specific value
> - `screenshot` — Take a picture
> - `custom` — Something special not in this list

```python
class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    HEALED = "healed"
    SKIPPED = "skipped"
```
> **Lines 48-54:** The possible outcomes for a test step:
> - `pending` — Hasn't started yet
> - `running` — Currently in progress
> - `passed` — Worked perfectly on the first try
> - `failed` — Didn't work even after trying all backup methods
> - `healed` — Failed at first, but a backup method worked
> - `skipped` — Deliberately skipped

```python
class AIProvider(str, Enum):
    GEMINI = "GEMINI"
    CLAUDE = "CLAUDE"
```
> **Lines 57-59:** Which AI service to use. Only two options: Google's Gemini or Anthropic's Claude.

---

### Data Models (Structured Forms) — Lines 66 onward

```python
class Locator(BaseModel):
    strategy: LocatorStrategy
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    description: str = ""
```
> **Lines 66-71:** A **Locator** is like directions to find one specific button/field on a webpage.
> - `strategy` — Which method to use (test_id, id, css, etc.)
> - `value` — The actual address (like `"#login-button"` or `"Login"`)
> - `confidence` — How sure the AI is (0.0 = not sure at all, 1.0 = absolutely certain)
> - `description` — A human-readable note about why this locator was chosen

```python
    def to_playwright(self) -> str:
        match self.strategy:
            case LocatorStrategy.TEST_ID:
                return f'page.get_by_test_id("{self.value}")'
            case LocatorStrategy.ID:
                return f'page.locator("#{self.value}")'
            ...
```
> **Lines 73-89:** The `to_playwright()` method converts this locator into actual code that Playwright (the browser tool) understands. For example, if the strategy is `ID` and the value is `login-button`, it outputs `page.locator("#login-button")` — real code that tells the browser "find the element with this ID."

```python
class LocatorSet(BaseModel):
    element_name: str
    primary: Locator
    secondary: Optional[Locator] = None
    tertiary: Optional[Locator] = None
```
> **Lines 92-98:** A **LocatorSet** holds THREE locators for the same element — a primary (best), secondary (backup), and tertiary (last resort). `Optional` means the secondary and tertiary might not exist.

```python
    def ranked(self) -> list[Locator]:
        return [loc for loc in [self.primary, self.secondary, self.tertiary] if loc]
```
> **Lines 100-102:** The `ranked()` method returns all available locators in priority order, skipping any that are missing (`None`).

```python
class TestStepInput(BaseModel):
    step_number: int
    intent: str
    action_type: ActionType = ActionType.CLICK
    input_data: Optional[str] = None
    expected_result: str
    page_url: Optional[str] = None
```
> **Lines 109-116:** A **TestStepInput** is ONE step in a test, BEFORE it's been executed.
> - `step_number` — Which step (1, 2, 3...)
> - `intent` — What to do, in plain English ("Click the Login button")
> - `action_type` — The specific action (click, fill, etc.)
> - `input_data` — Data to type (e.g., "standard_user" for a username field)
> - `expected_result` — What should happen ("Products page loads")

```python
class TestStepResult(BaseModel):
    step_input: TestStepInput
    status: StepStatus = StepStatus.PENDING
    locators_used: Optional[LocatorSet] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    actual_result: str = ""
    error_message: str = ""
    healing_attempts: int = 0
    duration_ms: float = 0.0
```
> **Lines 119-133:** A **TestStepResult** is what happened AFTER executing a step.
> - `step_input` — The original step definition
> - `status` — Did it pass, fail, or get healed?
> - `locators_used` — Which locators were tried
> - `screenshot_before/after` — Photos of the page before and after the action
> - `actual_result` — What actually happened
> - `error_message` — If it failed, what went wrong
> - `healing_attempts` — How many backup locators were tried
> - `duration_ms` — How long it took (in milliseconds)

```python
class TestCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str = ""
    target_url: str
    steps: list[TestStepInput] = []
```
> **Lines 140-149:** A **TestCase** is a complete test (like "Valid User Login") made up of multiple steps.
> - `id` — A random unique identifier (like "a3f2b8c1")
> - `name` — Human-readable name
> - `steps` — The ordered list of steps to execute

```python
class TestCaseResult(BaseModel):
    test_case: TestCase
    step_results: list[TestStepResult] = []
    overall_status: StepStatus = StepStatus.PENDING

    @property
    def passed_steps(self) -> int:
        return sum(1 for s in self.step_results if s.status == StepStatus.PASSED)
```
> **Lines 153-173:** A **TestCaseResult** is the full result of running a test case.
> - `test_case` — The original test definition
> - `step_results` — Results for each step
> - `overall_status` — The combined result
> - `passed_steps` / `failed_steps` / `healed_steps` — Convenient counters (calculated automatically by counting matching steps)

```python
class PageState(BaseModel):
    url: str
    title: str
    screenshot_path: str
    screenshot_base64: Optional[str] = None
    dom_html: str
    minified_html: str = ""
    visible_text: str = ""
```
> **Lines 180-189:** A **PageState** is a complete snapshot of what a web page looks like at one moment.
> - `url` — The web address
> - `title` — The page title
> - `screenshot_path` — Where the screenshot photo is saved on disk
> - `screenshot_base64` — The screenshot as encoded text (for sending to AI)
> - `dom_html` — The full page code (HTML)
> - `minified_html` — A cleaned-up, shorter version of the HTML
> - `visible_text` — Just the text you can see on the page (no code)

```python
class AppConfig(BaseModel):
    ai_provider: AIProvider = AIProvider.CLAUDE
    gemini_api_key: str = ""
    claude_api_key: str = ""
    headless: bool = False
    viewport_width: int = 1920
    ...
```
> **Lines 243-285:** The **AppConfig** holds ALL settings for the entire program. It has 33 fields covering AI keys, browser settings, self-healing options, output preferences, and model configurations. Think of it as the master control panel.

---

# 6. `core/agent.py` — The Boss

**Analogy:** This is the **project manager**. It doesn't do any of the actual work itself — instead, it delegates tasks to specialists and makes sure everything happens in the right order.

```python
class AutonomousTestAgent:
    def __init__(self, config: AppConfig):
        self.ai_engine = AIEngine(config)
        self.locator_engine = LocatorEngine(self.ai_engine)
        self.state_capture = StateCaptureEngine(...)
        self.action_executor = ActionExecutor(...)
        self.requirement_parser = RequirementParser(self.ai_engine)
        self.rag_engine = RAGEngine(...) if config.rag_enabled else None
        self.script_gen = ScriptGenerator(...)
        self.docx_gen = DocxGenerator(...)
        self.report_gen = ReportGenerator(...)
        self._executor = ThreadPoolExecutor(max_workers=3)
```
> **Lines 58-87:** When the Boss is created, it immediately hires all its specialists:
> - **AI Engine** — The brain that talks to Google/Anthropic
> - **Locator Engine** — The element finder (uses the AI Engine)
> - **State Capture** — The camera
> - **Action Executor** — The hands that click
> - **Requirement Parser** — The document reader (also uses the AI Engine)
> - **RAG Engine** — The memory system (only created if enabled)
> - **3 Generators** — The report writers (script, Word, HTML)
> - **Thread Pool with 3 workers** — Three extra workers that can write reports simultaneously

```python
    async def run(self, requirement_file, requirement_text, target_url, knowledge_dir):
```
> **Line 89:** The main `run` method — this is the full pipeline.

```python
        # Step 1: Ingest knowledge base
        if knowledge_dir and self.rag_engine:
            chunks = self.rag_engine.ingest_directory(knowledge_dir)
```
> **Lines 121-125:** If a knowledge folder was provided, feed all the documents into the memory system. This is like giving the AI a reference book before a test.

```python
        # Step 2: Parse requirements
        test_cases = self._parse_requirements(requirement_file, requirement_text, url)
```
> **Lines 127-129:** Read the requirement document and convert it into structured test cases.

```python
        # Step 3: Execute in browser
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.config.headless, slow_mo=self.config.slow_mo)
            context = await browser.new_context(viewport={...})

            for tc in test_cases:
                result = await self._execute_test_case(context, tc)
                results.append(result)

            await context.close()
            await browser.close()
```
> **Lines 133-151:** Open a real browser, create a browsing session, and execute each test case one by one. After all tests finish, close the browser. `async with` means "open this resource, use it, and make sure it gets closed even if something goes wrong."

```python
        # Step 4: Generate artifacts in parallel
        self._generate_artifacts_parallel(results)
```
> **Lines 153:** Hand the results to the three report writers, who work simultaneously to create the .py, .docx, and .html files.

### The `_execute_test_case` Method (Lines 229-313)

This is where each test case actually runs:

```python
        page = await context.new_page()
        await page.goto(test_case.target_url, wait_until="networkidle")
```
> Open a new browser tab and navigate to the website. `wait_until="networkidle"` means "wait until the page has fully loaded (no more data being fetched)."

```python
        for step in test_case.steps:
            # 1. Take a photo and read the HTML
            state = await self.state_capture.capture(page, f"step_{step.step_number}")

            # 2. Check the memory for helpful context
            rag_context = self.rag_engine.get_context_for_step(step.intent)

            # 3. Ask AI to find the element
            locators = self.locator_engine.identify_locators(state, step)

            # 4. Click/type/check with self-healing
            step_result = await self.action_executor.execute_step(page, step, locators)

            result.step_results.append(step_result)
```
> **Lines 254-286:** For EACH step in the test:
> 1. **Camera** takes a screenshot and reads the page code
> 2. **Memory** searches for relevant info from user manuals
> 3. **Element Finder** asks AI "Where is this button?" and gets 3 ranked locators
> 4. **Hands** try to perform the action, using backup locators if the first one fails
> 5. Save the result

### Parallel Artifact Generation (Lines 315-338)

```python
    def _generate_artifacts_parallel(self, results):
        futures = []
        for result in results:
            futures.append(self._executor.submit(self.script_gen.generate, result))
            futures.append(self._executor.submit(self.docx_gen.generate, result))
            futures.append(self._executor.submit(self.report_gen.generate, result))

        for future in futures:
            path = future.result(timeout=30)
```
> **Lines 315-338:** For each test result, submit three jobs to the worker pool: generate a script, generate a Word doc, generate an HTML report. All three run at the same time (in parallel). Wait up to 30 seconds for each to finish.

---

# 7. `core/ai_engine.py` — The AI Brain

**Analogy:** This is the **translator** who talks to the AI services. When we need AI help, we send our question through this engine. It knows how to speak both "Gemini language" and "Claude language."

```python
class AIEngine:
    def __init__(self, config: AppConfig):
        self._init_providers()
```
> **Lines 22-29:** Create the engine and set up connections to AI providers.

```python
    def _init_providers(self):
        if self.config.gemini_api_key:
            genai.configure(api_key=self.config.gemini_api_key)
        if self.config.claude_api_key:
            self._claude_client = anthropic.Anthropic(api_key=self.config.claude_api_key)
```
> **Lines 31-43:** If we have a Gemini key, set up the Gemini connection. If we have a Claude key, set up the Claude connection. You can have both, one, or neither (but at least one is required).

```python
    def infer(self, prompt, images=None, provider=None, temperature=None, max_tokens=None):
```
> **Line 45:** The main method. `prompt` is the question we ask the AI. `images` are screenshots (optional). It returns the AI's answer.

```python
        if active_provider == AIProvider.GEMINI:
            response = self._infer_gemini(request)
        elif active_provider == AIProvider.CLAUDE:
            response = self._infer_claude(request)
```
> **Lines 96-101:** Route to the right AI. Like choosing which phone number to call depending on whether you want to talk to Google or Anthropic.

### Gemini Call (Lines 116-154)

```python
    def _infer_gemini(self, request):
        model = genai.GenerativeModel(request.model)

        parts = []
        for img_b64 in request.images:
            img_bytes = base64.b64decode(img_b64)
            parts.append({"mime_type": "image/jpeg", "data": img_bytes})
        parts.append(request.prompt)

        response = model.generate_content(parts, generation_config=generation_config)
        return AIResponse(content=response.text, ...)
```
> This creates a Gemini AI model, packages up the images and text question into `parts`, sends everything to Google, and returns the answer. Gemini can look at images AND read text at the same time (this is called "multimodal").

### Claude Call (Lines 156-194)

```python
    def _infer_claude(self, request):
        content_blocks = []
        for img_b64 in request.images:
            content_blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}
            })
        content_blocks.append({"type": "text", "text": request.prompt})

        response = self._claude_client.messages.create(
            model=request.model,
            messages=[{"role": "user", "content": content_blocks}],
        )
        return AIResponse(content=response.content[0].text, ...)
```
> Same idea but for Claude. The format is slightly different — Claude expects "content blocks" with labeled types ("image" or "text").

### JSON Helper (Lines 208-227)

```python
    def infer_json(self, prompt, images=None, provider=None):
        response = self.infer(prompt, images, provider)
        text = response.content.strip()
        if text.startswith("```"):
            lines = [l for l in text.split("\n") if not l.strip().startswith("```")]
            text = "\n".join(lines)
        return json.loads(text)
```
> A convenience method. It sends a question, gets a text answer, strips away any markdown formatting (the ``` marks that AI sometimes wraps its answers in), and converts the text into a structured Python dictionary. This is used whenever we need the AI to return structured data (like locator details).

---

# 8. `core/locator_engine.py` — The Element Finder

**Analogy:** This is the **detective** who shows a screenshot to the AI and asks "Where is the Login button? Give me three ways to find it."

### The Prompt Template (Lines 24-73)

```python
LOCATOR_PROMPT_TEMPLATE = """You are an expert Playwright test automation engineer.

## Task
Analyze the provided screenshot and HTML to identify the UI element described below.
Return a JSON object with **three** Playwright locator strategies ranked by reliability.

## Target Element
- **Intent:** {intent}
- **Action:** {action_type}

## HTML (minified)
```html
{html_snippet}
```

## Instructions
1. Study the screenshot to visually locate the element.
2. Cross-reference with the HTML to find the best locators.
3. Return ONLY valid JSON...

Prioritize: data-testid > id > aria-label > CSS > XPath > visual text.
"""
```
> **Lines 24-73:** This is a carefully crafted question for the AI. Think of it as a **form letter** with blanks to fill in. The blanks (`{intent}`, `{action_type}`, `{html_snippet}`) get replaced with real values for each element we're looking for. The AI is told:
> 1. Look at the screenshot
> 2. Look at the HTML code
> 3. Give us exactly 3 ways to find the element
> 4. Prefer stable methods (like `data-testid`) over fragile ones (like XPath)

### The `identify_locators` Method (Lines 82-115)

```python
    def identify_locators(self, page_state, step, provider=None):
        prompt = LOCATOR_PROMPT_TEMPLATE.format(
            intent=step.intent,
            action_type=step.action_type.value,
            html_snippet=page_state.minified_html[:15000],
            ...
        )
        images = [page_state.screenshot_base64]

        try:
            data = self.ai.infer_json(prompt, images=images)
            return self._parse_locator_response(data)
        except:
            return self._fallback_locator(step)
```
> Fill in the template with the actual step info and HTML, attach the screenshot, send it to the AI, and parse the response into a `LocatorSet`. If anything goes wrong (AI returns garbage, network error), use a simple fallback locator based on the step's text.

### The Fallback (Lines 151-163)

```python
    def _fallback_locator(self, step):
        return LocatorSet(
            element_name=step.intent,
            primary=Locator(
                strategy=LocatorStrategy.VISUAL,
                value=step.intent,
                confidence=0.3,
            ),
        )
```
> If the AI completely fails, create a bare-minimum locator: just search for the text on the page. Confidence is only 0.3 (30%) because this is a guess.

---

# 9. `core/action_executor.py` — The Hands That Click

**Analogy:** This is the **robot arm** that actually interacts with the website. If it can't grab something with its right hand (primary locator), it tries the left hand (secondary), then a third method (tertiary). This is the **self-healing** in action.

### The Self-Healing Loop (Lines 47-140)

```python
    async def execute_step(self, page, step, locators):
        # 1. Take a "before" photo
        before_bytes = await page.screenshot(full_page=False)
        result.screenshot_before = save_screenshot(before_bytes, ...)

        # 2. Get ranked locators: [primary, secondary, tertiary]
        ranked = locators.ranked()

        # 3. Try each one
        for idx, locator in enumerate(ranked):
            try:
                await self._perform_action(page, step, locator)

                # It worked!
                if idx == 0:
                    result.status = StepStatus.PASSED    # Primary worked = PASSED
                else:
                    result.status = StepStatus.HEALED    # Backup worked = HEALED
                break  # Stop trying

            except:
                # This locator didn't work, try the next one
                continue

        else:
            # None of them worked
            result.status = StepStatus.FAILED

        # 4. Take an "after" photo
        after_bytes = await page.screenshot(full_page=False)
        result.screenshot_after = save_screenshot(after_bytes, ...)
```
> The core of self-healing:
> 1. Take a "before" photo
> 2. Try the best locator first
> 3. If it works → mark as PASSED and stop
> 4. If it fails → try the next locator
> 5. If a backup works → mark as HEALED (it healed itself!)
> 6. If ALL fail → mark as FAILED
> 7. Take an "after" photo
>
> The `for/else` is special Python: the `else` block runs only if the loop finished WITHOUT a `break` (meaning nothing worked).

### Performing the Action (Lines 142-208)

```python
    async def _perform_action(self, page, step, locator):
        pw_locator = self._resolve_locator(page, locator)
        await pw_locator.wait_for(state="visible", timeout=self.action_timeout)

        match step.action_type:
            case ActionType.CLICK:
                await pw_locator.click()
            case ActionType.FILL:
                await pw_locator.fill(step.input_data or "")
            case ActionType.NAVIGATE:
                await page.goto(url, wait_until="networkidle")
            case ActionType.ASSERT_TEXT:
                actual_text = await pw_locator.text_content()
                if expected not in actual_text:
                    raise AssertionError("Text mismatch!")
            ...
```
> First, convert our locator into a Playwright locator object. Wait for the element to be visible on screen. Then, depending on the action type:
> - **click** → Click it
> - **fill** → Type text into it
> - **navigate** → Go to a URL
> - **assert_text** → Read the element's text and check if it matches what we expect. If not, raise an error (which triggers the self-healing loop to try the next locator).

### Resolving Locators (Lines 210-232)

```python
    def _resolve_locator(self, page, locator):
        match locator.strategy:
            case LocatorStrategy.TEST_ID:
                return page.get_by_test_id(locator.value)
            case LocatorStrategy.ID:
                return page.locator(f"#{locator.value}")
            case LocatorStrategy.ARIA:
                return page.get_by_label(locator.value)
            case LocatorStrategy.VISUAL:
                return page.get_by_text(locator.value)
```
> Convert our generic locator into a specific Playwright command:
> - **TEST_ID** → `page.get_by_test_id("login")` — Find by test ID attribute
> - **ID** → `page.locator("#login-button")` — Find by HTML ID (the `#` means "ID")
> - **ARIA** → `page.get_by_label("Login")` — Find by accessibility label
> - **VISUAL** → `page.get_by_text("Login")` — Find by the visible text on screen

---

# 10. `core/state_capture.py` — The Camera

**Analogy:** This is a **camera + scanner** that takes a picture of the website AND reads all its underlying code.

```python
    async def capture(self, page, step_label="page", full_page=True):
        # Wait for page to fully load
        await page.wait_for_load_state("networkidle", timeout=10000)

        # Take screenshot
        screenshot_bytes = await page.screenshot(full_page=full_page)
        screenshot_path = save_screenshot(screenshot_bytes, self.output_dir, filename)
        screenshot_b64 = prepare_for_ai(screenshot_bytes)

        # Read the HTML code
        dom_html = await page.content()
        minified = minify_html(dom_html)
        visible_text = extract_visible_text(dom_html)

        # Package everything together
        state = PageState(
            url=page.url,
            title=await page.title(),
            screenshot_path=screenshot_path,
            screenshot_base64=screenshot_b64,
            dom_html=dom_html,
            minified_html=minified,
            visible_text=visible_text,
        )
        return state
```
> For each step:
> 1. **Wait** for the page to finish loading
> 2. **Take a screenshot** — save it to disk AND prepare a smaller version for the AI
> 3. **Read the HTML** — get the full page code, then clean it up (minify) and extract just the visible text
> 4. **Bundle everything** into a `PageState` object that gets passed to the Element Finder

---

# 11. `core/requirement_parser.py` — The Document Reader

**Analogy:** You hand this module a Word document, Excel file, or plain text file and it turns it into a structured list of "do this, then do this, then check this."

### Reading Word Files (Lines 99-116)

```python
    def _extract_docx(self, path):
        doc = DocxDocument(str(path))
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    paragraphs.append(" | ".join(cells))
        return "\n".join(paragraphs)
```
> Open the Word document. Read every paragraph and every table cell. Join table cells with `|` between them. Return everything as one big text string.

### Reading Excel Files (Lines 118-142)

```python
    def _extract_xlsx(self, path):
        wb = openpyxl.load_workbook(str(path), data_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for row_idx, row in enumerate(ws.iter_rows(values_only=True)):
                # First row = column headers
                # Other rows = data formatted as "Header: Value; Header: Value"
```
> Open the Excel workbook. For each sheet, read the header row, then format each data row as "Column Name: Value; Column Name: Value." This turns a spreadsheet into readable text.

### AI-Powered Parsing (Lines 148-191)

```python
    def _ai_parse(self, raw_text, target_url, source):
        chunks = self._chunk_text(raw_text, max_chars=8000)
        for chunk in chunks:
            prompt = PARSE_PROMPT_TEMPLATE.format(requirement_text=chunk)
            data = self.ai.infer_json(prompt)
            # Convert AI response into TestCase objects
```
> The raw text is too unstructured for a computer to understand directly. So we:
> 1. **Break it into chunks** (max 8000 characters each) in case it's very long
> 2. **Send each chunk to the AI** with instructions: "Parse this into structured test steps"
> 3. **The AI returns JSON** with step numbers, actions, data, and expected results
> 4. **Convert that JSON into TestCase objects** that the rest of the program can use

---

# 12. `generators/script_generator.py` — The Script Writer

**Analogy:** After the test runs, this module **writes a Python file** that can replay the exact same test. It's like a court reporter who writes down everything that happened so it can be repeated.

```python
    def generate(self, test_result):
        script = self._build_script(test_result)
        filepath.write_text(script, encoding="utf-8")
```
> Build the script text, then save it to a `.py` file.

### What the Generated Script Looks Like

```python
"""
Auto-Generated Playwright Test Script
Test Case : Valid User Login
Generated  : 2026-02-16 14:00:00
"""
from playwright.sync_api import Playwright, sync_playwright, expect

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_context().new_page()
    page.goto("https://www.saucedemo.com")

    # Step 1: Enter the username
    # Expected: Username field displays "standard_user"
    page.locator("#user-name").fill("standard_user")
    # --- Backup locators (self-healing) ---
    # Backup 2 (aria): page.get_by_label("Username")

    # Step 2: Click the Login button
    page.locator("#login-button").click()

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
```
> The generator creates clean, runnable code. Each step has:
> - A comment saying what it does and what's expected
> - The actual Playwright command using the primary locator
> - Commented-out backup locators (in case you need to edit later)

---

# 13. `generators/docx_generator.py` — The Word Report Writer

**Analogy:** This creates a **formal test case document** in Microsoft Word format — the kind you'd hand to a QA manager or attach to a Jira ticket.

```python
    def generate(self, test_result):
        doc = Document()
        self._add_title(doc, tc.name)
        self._add_metadata(doc, test_result)
        self._add_steps_table(doc, test_result)
        self._add_summary(doc, test_result)
        doc.save(str(filepath))
```
> Create a new Word document, add four sections, and save it.

### The Four Sections:

1. **Title** — Test case name, centered, with "Generated by Self-Healing Autonomous Test Agent" subtitle

2. **Metadata Table** — A 2-column table with: Test ID, Description, Preconditions, URL, Source File, Total Steps, Overall Status

3. **Steps Table** — A 6-column table with each step:
   - Step number, Action, Input Data, Expected Result, Status (color-coded: green=pass, red=fail, yellow=healed), Locator used
   - Plus embedded before/after screenshots for each step

4. **Summary** — Bullet points: Total Steps, Passed, Failed, Healed, Duration, Healing Attempts

---

# 14. `generators/report_generator.py` — The Dashboard Builder

**Analogy:** This creates a **beautiful web dashboard** you can open in any browser. It looks like a modern analytics page with colored cards, charts, and detailed step-by-step results.

### The HTML Template (Lines 18-202)

The report uses a dark theme with these colors:
- Background: dark navy blue (`#0f172a`)
- Cards: slightly lighter blue (`#1e293b`)
- Passed: green (`#22c55e`)
- Failed: red (`#ef4444`)
- Healed: yellow (`#eab308`)

The layout has:
- **Statistics cards at the top** — Total Steps, Passed, Failed, Healed, Duration, AI Tokens
- **Step-by-step cards** — Each step shows what happened, which locator was used, and whether it passed/failed/healed
- **AI Usage table at the bottom** — Shows how many AI tokens each step consumed and how fast the AI responded

### JSON Report (Lines 333-349)

```python
    def _save_json_report(self, test_result, filepath):
        data = {
            "test_case": test_result.test_case.model_dump(mode="json"),
            "step_results": [...],
            "summary": {...},
            "ai_usage": self._ai_log,
        }
        filepath.write_text(json.dumps(data, indent=2))
```
> In addition to the HTML dashboard, a machine-readable JSON file is also saved. This is useful for automated systems (like CI/CD pipelines) that need to parse the results programmatically.

---

# 15. `knowledge/rag_engine.py` — The Memory

**Analogy:** Imagine giving the AI a **reference book** before it takes a test. Instead of guessing where buttons are, it can look up the answer. RAG = Retrieval Augmented Generation — a fancy way of saying "look stuff up before answering."

### How Documents Get Stored (Lines 63-95)

```python
    def ingest_document(self, file_path):
        # 1. Read the document (Word or text file)
        text = path.read_text(encoding="utf-8")

        # 2. Break it into small chunks
        chunks = self._splitter.split_text(text)

        # 3. Store chunks in the database with IDs
        self._collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
```
> Read a document, break it into ~1000-character pieces (like tearing pages out of a book), and store each piece in a local database. The database also creates a mathematical representation (called an "embedding") of each piece, which allows for smart searching later.

### How Information Gets Retrieved (Lines 105-154)

```python
    def query(self, question, n_results=5):
        results = self._collection.query(query_texts=[question], n_results=5)
        # Returns the 5 most relevant chunks
```
> When the AI needs to find a specific element, we first search the memory: "What do we know about the checkout button?" The database finds the 5 most relevant chunks from all stored documents.

```python
    def get_context_for_step(self, intent, max_chars=3000):
        results = self.query(intent, n_results=3)
        # Format as readable text and return
```
> For each test step, retrieve the top 3 relevant knowledge chunks and format them into a text block that gets added to the AI's prompt. This gives the AI extra context to make better decisions.

---

# 16. `utils/dom_utils.py` — The HTML Cleaner

**Analogy:** A typical web page has THOUSANDS of lines of HTML code. Most of it (JavaScript, CSS, invisible metadata) is useless noise for finding buttons. This module is like a **janitor** who cleans up the HTML, keeping only the useful parts.

### What Gets Removed

```python
REMOVE_TAGS = {"script", "style", "noscript", "svg", "path", "meta", "link"}
```
> These tags are completely deleted:
> - `<script>` — JavaScript code (not useful for finding buttons)
> - `<style>` — CSS styling code
> - `<noscript>` — Content for browsers without JavaScript
> - `<svg>`, `<path>` — Vector graphics code
> - `<meta>`, `<link>` — Page metadata

### What Gets Kept

```python
KEEP_ATTRIBUTES = {
    "id", "class", "name", "type", "value", "placeholder",
    "href", "src", "alt", "title", "role", "aria-label",
    "data-testid", "data-test", "data-cy", ...
}
```
> On the elements that remain, only these attributes are kept. For example, `<button id="login" class="btn" style="color:red" onclick="handleClick()">` becomes `<button id="login" class="btn">`. The styling and JavaScript are removed, but the ID and class (which help find the element) are preserved.

### The Minification Process

```python
def minify_html(html, max_length=50000):
    # 1. Remove script, style, svg, etc.
    # 2. Remove HTML comments
    # 3. Keep only useful attributes on remaining elements
    # 4. Collapse all extra whitespace
    # 5. Truncate to 50,000 characters max
```
> A typical page might have 200,000 characters of HTML. After cleaning, it might be 10,000-20,000 characters — small enough to send to the AI without wasting tokens on noise.

### Extract Visible Text

```python
def extract_visible_text(html):
    text = re.sub(r"<[^>]+>", " ", html)  # Remove all tags
    return text.strip()[:10000]            # Keep first 10,000 chars
```
> Strip away ALL HTML tags, leaving just the text that a human would see on the page. Truncate to 10,000 characters.

---

# 17. `utils/screenshot_utils.py` — The Photo Editor

**Analogy:** The screenshots we take are large high-resolution images. Before sending them to the AI, we need to **resize** them (to save money on AI tokens) and **convert** them to a format the AI can understand.

```python
def resize_screenshot(screenshot_bytes, max_width=1280, max_height=1024, quality=85):
    img = Image.open(io.BytesIO(screenshot_bytes))
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    img_rgb = img.convert("RGB")
    img_rgb.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()
```
> Open the screenshot, shrink it if it's too big (keeping proportions), convert to JPEG format (smaller file size), and return the compressed bytes. LANCZOS is a high-quality resizing algorithm.

```python
def prepare_for_ai(screenshot_bytes, max_width=1280, max_height=1024):
    resized = resize_screenshot(screenshot_bytes, max_width, max_height)
    return screenshot_to_base64(resized)
```
> Resize the screenshot AND convert it to base64 text (a text representation of the image that can be sent over the internet to the AI). This is the function that gets called right before sending screenshots to Gemini or Claude.

```python
def save_screenshot(screenshot_bytes, output_dir, filename):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    file_path = Path(output_dir) / filename
    file_path.write_bytes(screenshot_bytes)
    return str(file_path)
```
> Save the raw screenshot to disk. Create the output folder if it doesn't exist. Return the file path so other parts of the program know where to find it.

---

# 18. `requirements.txt` — The Shopping List

**Analogy:** Before you can cook a recipe, you need to buy the ingredients. This file lists all the Python packages (ingredients) the project needs, with exact versions so nothing breaks.

```
playwright==1.49.1          # The browser automation tool
anthropic==0.42.0           # Talks to Claude AI
google-generativeai==0.8.4  # Talks to Gemini AI
python-docx==1.1.2          # Reads/writes Word documents
openpyxl==3.1.5             # Reads Excel spreadsheets
chromadb==0.5.23            # The memory database (for RAG)
langchain-text-splitters==0.3.4  # Breaks documents into chunks
Pillow==11.1.0              # Image processing (resize screenshots)
PyYAML==6.0.2               # Reads the config.yaml settings file
python-dotenv==1.0.1        # Reads the .env secrets file
pydantic==2.10.4            # Data validation (the blueprints)
jinja2==3.1.5               # Template rendering
rich==13.9.4                # Pretty terminal output
aiofiles==24.1.0            # Async file operations
tenacity==9.0.0             # Retry logic
```

You install everything with: `pip install -r requirements.txt`

---

## Quick Reference: How Everything Connects

```
YOU type a command
  ↓
main.py reads your command
  ↓
config_loader.py reads settings (.env + config.yaml)
  ↓
agent.py (The Boss) starts the pipeline:
  ↓
  ├─ requirement_parser.py reads your document
  │    └─ ai_engine.py asks AI to structure the requirements
  │
  ├─ rag_engine.py loads user manuals into memory (optional)
  │
  ├─ FOR EACH TEST STEP:
  │    ├─ state_capture.py takes a screenshot + reads HTML
  │    │    ├─ dom_utils.py cleans up the HTML
  │    │    └─ screenshot_utils.py resizes the screenshot
  │    │
  │    ├─ locator_engine.py asks AI "Where is this element?"
  │    │    └─ ai_engine.py sends screenshot + HTML to Gemini/Claude
  │    │
  │    └─ action_executor.py clicks/types/checks with self-healing
  │         └─ If primary fails → try secondary → try tertiary → or FAIL
  │
  └─ THREE REPORTS generated in parallel:
       ├─ script_generator.py → Python file (.py)
       ├─ docx_generator.py → Word document (.docx)
       └─ report_generator.py → HTML dashboard + JSON (.html + .json)
  ↓
Results shown in your terminal as a colored table
Output files saved in the output/ folder
```

---

*End of Code Explained — Plain Language Guide*
*Every file, every function, every important line has been explained above.*
