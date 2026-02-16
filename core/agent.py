"""
Self-Healing Autonomous Test Agent — Main Orchestrator.

This is the central controller that ties together all subsystems:
1. Requirement parsing
2. RAG knowledge base
3. Playwright browser automation
4. AI-driven locator identification
5. Self-healing action execution
6. Parallel artifact generation (script, docx, report)

The agent consumes unstructured requirements and produces:
- Executed test results
- Python Playwright scripts
- Word test case documents
- HTML/JSON execution reports
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from core.action_executor import ActionExecutor
from core.ai_engine import AIEngine
from core.locator_engine import LocatorEngine
from core.requirement_parser import RequirementParser
from core.state_capture import StateCaptureEngine
from generators.docx_generator import DocxGenerator
from generators.report_generator import ReportGenerator
from generators.script_generator import ScriptGenerator
from knowledge.rag_engine import RAGEngine
from models.schemas import (
    AppConfig,
    StepStatus,
    TestCase,
    TestCaseResult,
    TestStepResult,
)

logger = logging.getLogger(__name__)


class AutonomousTestAgent:
    """
    The top-level orchestrator that runs the full autonomous test loop.

    Usage:
        agent = AutonomousTestAgent(config)
        results = await agent.run(requirement_file="input/requirements.docx")
    """

    def __init__(self, config: AppConfig):
        self.config = config

        # Core engines
        self.ai_engine = AIEngine(config)
        self.locator_engine = LocatorEngine(self.ai_engine)
        self.state_capture = StateCaptureEngine(
            output_dir=f"{config.output_dir}/screenshots"
        )
        self.action_executor = ActionExecutor(
            max_retries=config.max_healing_retries,
            action_timeout=config.timeout,
            output_dir=f"{config.output_dir}/screenshots",
        )
        self.requirement_parser = RequirementParser(self.ai_engine)

        # Knowledge base
        self.rag_engine = RAGEngine(
            persist_dir=f"{config.output_dir}/vectorstore",
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        ) if config.rag_enabled else None

        # Artifact generators
        self.script_gen = ScriptGenerator(f"{config.output_dir}/scripts")
        self.docx_gen = DocxGenerator(f"{config.output_dir}/testcases")
        self.report_gen = ReportGenerator(f"{config.output_dir}/reports")

        # Thread pool for parallel artifact generation
        self._executor = ThreadPoolExecutor(max_workers=3)

    async def run(
        self,
        requirement_file: Optional[str] = None,
        requirement_text: Optional[str] = None,
        target_url: Optional[str] = None,
        knowledge_dir: Optional[str] = None,
    ) -> list[TestCaseResult]:
        """
        Execute the full autonomous test pipeline.

        Parameters
        ----------
        requirement_file : str, optional
            Path to a .docx or .xlsx requirement document.
        requirement_text : str, optional
            Raw requirement text (alternative to file).
        target_url : str, optional
            Override the target URL from config.
        knowledge_dir : str, optional
            Directory containing user manuals for RAG ingestion.

        Returns
        -------
        list[TestCaseResult] with full execution details.
        """
        url = target_url or self.config.target_url
        logger.info("=" * 60)
        logger.info("AUTONOMOUS TEST AGENT — Starting pipeline")
        logger.info("Target URL: %s", url)
        logger.info("AI Provider: %s", self.config.ai_provider.value)
        logger.info("=" * 60)

        # Step 1: Ingest knowledge base (if provided)
        if knowledge_dir and self.rag_engine:
            logger.info("Ingesting knowledge base from: %s", knowledge_dir)
            chunks = self.rag_engine.ingest_directory(knowledge_dir)
            logger.info("Ingested %d knowledge chunks", chunks)

        # Step 2: Parse requirements into test cases
        test_cases = self._parse_requirements(requirement_file, requirement_text, url)
        logger.info("Parsed %d test case(s)", len(test_cases))

        # Step 3: Execute each test case in the browser
        results = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=self.config.headless,
                slow_mo=self.config.slow_mo,
            )
            context = await browser.new_context(
                viewport={
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height,
                },
            )

            for tc in test_cases:
                result = await self._execute_test_case(context, tc)
                results.append(result)

            await context.close()
            await browser.close()

        # Step 4: Generate artifacts in parallel
        self._generate_artifacts_parallel(results)

        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETE — %d test case(s) executed", len(results))
        for r in results:
            logger.info(
                "  %s: %s (passed=%d, failed=%d, healed=%d)",
                r.test_case.name,
                r.overall_status.value,
                r.passed_steps,
                r.failed_steps,
                r.healed_steps,
            )
        logger.info("=" * 60)

        return results

    async def run_single_step(
        self,
        target_url: str,
        intent: str,
        action_type: str = "click",
        input_data: Optional[str] = None,
    ) -> TestStepResult:
        """
        Execute a single step (useful for interactive / demo mode).
        """
        from models.schemas import ActionType, TestStepInput

        step = TestStepInput(
            step_number=1,
            intent=intent,
            action_type=ActionType(action_type),
            input_data=input_data,
            expected_result="Step completes successfully",
        )

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.config.headless)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(target_url, wait_until="networkidle")

            # Capture state
            state = await self.state_capture.capture(page, "single_step")

            # Get locators
            locators = self.locator_engine.identify_locators(state, step)
            logger.info("Locators: %s", locators)

            # Execute
            result = await self.action_executor.execute_step(page, step, locators)

            await context.close()
            await browser.close()

        return result

    # --------------------------------------------------------------------- #
    # Internal Pipeline Steps
    # --------------------------------------------------------------------- #

    def _parse_requirements(
        self,
        file_path: Optional[str],
        raw_text: Optional[str],
        target_url: str,
    ) -> list[TestCase]:
        """Parse requirements from file or raw text."""
        if file_path:
            return self.requirement_parser.parse_file(file_path, target_url)
        elif raw_text:
            return self.requirement_parser.parse_text(raw_text, target_url)
        else:
            raise ValueError("Provide either requirement_file or requirement_text")

    async def _execute_test_case(
        self,
        context: BrowserContext,
        test_case: TestCase,
    ) -> TestCaseResult:
        """Execute all steps of a single test case."""
        logger.info("--- Executing: %s ---", test_case.name)

        result = TestCaseResult(
            test_case=test_case,
            started_at=datetime.now(),
        )

        page = await context.new_page()

        # Navigate to starting URL
        if test_case.target_url:
            await page.goto(
                test_case.target_url,
                wait_until="networkidle",
                timeout=self.config.navigation_timeout,
            )

        total_start = time.perf_counter()

        for step in test_case.steps:
            logger.info("Step %d/%d: %s", step.step_number, len(test_case.steps), step.intent)

            # Capture current page state
            state = await self.state_capture.capture(
                page, f"step_{step.step_number}"
            )

            # Augment with RAG context if available
            rag_context = ""
            if self.rag_engine:
                rag_context = self.rag_engine.get_context_for_step(step.intent)

            # Identify locators via AI
            locators = self.locator_engine.identify_locators(state, step)

            # Log AI usage for reporting
            self.report_gen.log_ai_usage(
                step_number=step.step_number,
                provider=self.config.ai_provider.value,
                tokens=0,  # Updated from actual response in production
                latency_ms=0,
                reasoning=f"Identified locators for: {step.intent}",
            )

            # Execute the action with self-healing
            step_result = await self.action_executor.execute_step(
                page, step, locators
            )
            step_result.ai_reasoning = rag_context[:500] if rag_context else ""

            result.step_results.append(step_result)
            result.total_healing_attempts += step_result.healing_attempts

            # Stop on critical failure if desired
            if step_result.status == StepStatus.FAILED:
                logger.warning(
                    "Step %d FAILED — continuing with remaining steps",
                    step.step_number,
                )

        result.total_duration_ms = (time.perf_counter() - total_start) * 1000
        result.completed_at = datetime.now()

        # Determine overall status
        if result.failed_steps > 0:
            result.overall_status = StepStatus.FAILED
        elif result.healed_steps > 0:
            result.overall_status = StepStatus.HEALED
        else:
            result.overall_status = StepStatus.PASSED

        await page.close()
        logger.info(
            "--- Test '%s' complete: %s (%.1f s) ---",
            test_case.name,
            result.overall_status.value,
            result.total_duration_ms / 1000,
        )
        return result

    def _generate_artifacts_parallel(self, results: list[TestCaseResult]) -> None:
        """Generate all artifacts in parallel using a thread pool."""
        futures = []

        for result in results:
            if self.config.generate_script:
                futures.append(
                    self._executor.submit(self.script_gen.generate, result)
                )
            if self.config.generate_docx:
                futures.append(
                    self._executor.submit(self.docx_gen.generate, result)
                )
            if self.config.generate_report:
                futures.append(
                    self._executor.submit(self.report_gen.generate, result)
                )

        for future in futures:
            try:
                path = future.result(timeout=30)
                logger.info("Artifact generated: %s", path)
            except Exception as exc:
                logger.error("Artifact generation failed: %s", exc)
