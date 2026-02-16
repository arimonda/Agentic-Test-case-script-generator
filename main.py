"""
Self-Healing Autonomous Test Agent — Entry Point.

Usage:
    # Run with a requirement document
    python main.py --requirements input/requirements.docx --url https://app.example.com

    # Run with inline requirement text
    python main.py --text "Login with valid credentials and verify dashboard" --url https://app.example.com

    # Run with knowledge base
    python main.py --requirements input/requirements.docx --url https://app.example.com --knowledge input/manuals/

    # Demo mode: execute a single step
    python main.py --demo --url https://app.example.com --intent "Click the Login button"
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from core.agent import AutonomousTestAgent
from core.config_loader import load_config

console = Console()


def setup_logging(level: str = "INFO") -> None:
    """Configure rich-formatted logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Self-Healing Autonomous Test Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--requirements", "-r",
        type=str,
        help="Path to requirement document (.docx or .xlsx)",
    )
    parser.add_argument(
        "--text", "-t",
        type=str,
        help="Inline requirement text (alternative to --requirements)",
    )
    parser.add_argument(
        "--url", "-u",
        type=str,
        help="Target application URL (overrides config)",
    )
    parser.add_argument(
        "--knowledge", "-k",
        type=str,
        help="Directory with user manuals for RAG ingestion",
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/config.yaml",
        help="Path to config YAML file",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode (single step execution)",
    )
    parser.add_argument(
        "--intent",
        type=str,
        help="Intent for demo mode (e.g., 'Click the Login button')",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["GEMINI", "CLAUDE"],
        help="Override AI provider",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    return parser.parse_args()


def display_banner() -> None:
    """Display application banner."""
    banner = Panel(
        "[bold cyan]Self-Healing Autonomous Test Agent[/bold cyan]\n"
        "[dim]AI-Powered Browser Testing with Computer Vision & Self-Healing Locators[/dim]",
        border_style="bright_blue",
        padding=(1, 2),
    )
    console.print(banner)


def display_results(results) -> None:
    """Display execution results in a rich table."""
    for result in results:
        tc = result.test_case
        table = Table(
            title=f"Results: {tc.name}",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Step", style="dim", width=6)
        table.add_column("Intent", width=40)
        table.add_column("Status", width=12)
        table.add_column("Healed", width=8)
        table.add_column("Duration", width=12)

        for sr in result.step_results:
            status_style = {
                "PASSED": "green",
                "FAILED": "red",
                "HEALED": "yellow",
            }.get(sr.status.value.upper(), "white")

            table.add_row(
                str(sr.step_input.step_number),
                sr.step_input.intent,
                f"[{status_style}]{sr.status.value.upper()}[/{status_style}]",
                str(sr.healing_attempts),
                f"{sr.duration_ms:.0f} ms",
            )

        console.print(table)

        # Summary
        status_color = {
            "PASSED": "green",
            "FAILED": "red",
            "HEALED": "yellow",
        }.get(result.overall_status.value.upper(), "white")

        console.print(
            f"\n  Overall: [{status_color}]{result.overall_status.value.upper()}[/{status_color}]"
            f"  |  Passed: {result.passed_steps}"
            f"  |  Failed: {result.failed_steps}"
            f"  |  Healed: {result.healed_steps}"
            f"  |  Duration: {result.total_duration_ms:.0f} ms\n"
        )


async def main() -> None:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.log_level)
    display_banner()

    # Load config
    config = load_config(config_path=args.config)

    # Apply CLI overrides
    if args.url:
        config.target_url = args.url
    if args.provider:
        from models.schemas import AIProvider
        config.ai_provider = AIProvider(args.provider.upper())
    if args.headless:
        config.headless = True

    # Validate
    if not config.target_url:
        console.print("[red]Error: No target URL specified. Use --url or set TARGET_URL in .env[/red]")
        sys.exit(1)

    if not config.claude_api_key and not config.gemini_api_key:
        console.print("[red]Error: No API keys configured. Set CLAUDE_API_KEY or GEMINI_API_KEY in .env[/red]")
        sys.exit(1)

    # Initialize agent
    agent = AutonomousTestAgent(config)

    if args.demo:
        # Demo mode: single step
        if not args.intent:
            console.print("[red]Error: --intent is required in demo mode[/red]")
            sys.exit(1)

        console.print(f"\n[bold]Demo Mode:[/bold] Executing single step: '{args.intent}'\n")
        result = await agent.run_single_step(
            target_url=config.target_url,
            intent=args.intent,
        )
        console.print(f"  Status: {result.status.value}")
        console.print(f"  Locator: {result.locators_used}")
        console.print(f"  Duration: {result.duration_ms:.0f} ms")
        if result.error_message:
            console.print(f"  [red]Error: {result.error_message}[/red]")

    else:
        # Full pipeline mode
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


if __name__ == "__main__":
    asyncio.run(main())
