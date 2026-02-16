"""
Self-Healing Action Executor.

Executes Playwright actions using ranked locators. If the primary
locator fails, it automatically retries with secondary and tertiary
locators before reporting a failure. This is the "self-healing" core.
"""

import logging
import time
from typing import Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from models.schemas import (
    ActionType,
    Locator,
    LocatorSet,
    StepStatus,
    TestStepInput,
    TestStepResult,
)
from utils.screenshot_utils import save_screenshot

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Executes browser actions with self-healing retry logic.

    For each action, it tries locators in priority order (primary ->
    secondary -> tertiary). If all fail, the step is marked FAILED.
    If a non-primary locator succeeds, the step is marked HEALED.
    """

    def __init__(
        self,
        max_retries: int = 3,
        action_timeout: int = 10000,
        output_dir: str = "output/screenshots",
    ):
        self.max_retries = max_retries
        self.action_timeout = action_timeout
        self.output_dir = output_dir

    async def execute_step(
        self,
        page: Page,
        step: TestStepInput,
        locators: LocatorSet,
    ) -> TestStepResult:
        """
        Execute a single test step with self-healing locator fallback.

        Returns a TestStepResult with status, timing, and healing info.
        """
        result = TestStepResult(
            step_input=step,
            locators_used=locators,
        )

        start_time = time.perf_counter()

        # Capture "before" screenshot
        try:
            before_bytes = await page.screenshot(full_page=False)
            result.screenshot_before = save_screenshot(
                before_bytes, self.output_dir,
                f"step{step.step_number}_before.png",
            )
        except Exception as exc:
            logger.warning("Could not capture before-screenshot: %s", exc)

        # Try each locator in priority order
        ranked = locators.ranked()
        last_error = None

        for idx, locator in enumerate(ranked):
            try:
                logger.info(
                    "Step %d: Trying %s locator (%s) — %s",
                    step.step_number,
                    locator.strategy.value,
                    locator.value,
                    step.intent,
                )
                await self._perform_action(page, step, locator)

                # Success
                result.locator_used_index = idx
                result.status = StepStatus.HEALED if idx > 0 else StepStatus.PASSED
                result.healing_attempts = idx
                result.actual_result = f"Action succeeded using {locator.strategy.value} locator"

                if idx > 0:
                    logger.info(
                        "Step %d HEALED: Primary failed, succeeded with %s (attempt %d)",
                        step.step_number,
                        locator.strategy.value,
                        idx + 1,
                    )
                else:
                    logger.info("Step %d PASSED with primary locator", step.step_number)

                break

            except (PlaywrightTimeout, Exception) as exc:
                last_error = str(exc)
                logger.warning(
                    "Step %d: %s locator failed: %s",
                    step.step_number,
                    locator.strategy.value,
                    last_error,
                )
                result.healing_attempts = idx + 1
                continue

        else:
            # All locators exhausted
            result.status = StepStatus.FAILED
            result.error_message = f"All {len(ranked)} locators failed. Last error: {last_error}"
            logger.error(
                "Step %d FAILED: All locators exhausted for '%s'",
                step.step_number,
                step.intent,
            )

        # Capture "after" screenshot
        try:
            after_bytes = await page.screenshot(full_page=False)
            result.screenshot_after = save_screenshot(
                after_bytes, self.output_dir,
                f"step{step.step_number}_after.png",
            )
        except Exception as exc:
            logger.warning("Could not capture after-screenshot: %s", exc)

        result.duration_ms = (time.perf_counter() - start_time) * 1000
        return result

    async def _perform_action(
        self,
        page: Page,
        step: TestStepInput,
        locator: Locator,
    ) -> None:
        """
        Execute the actual Playwright action for a given step and locator.
        """
        pw_locator = self._resolve_locator(page, locator)

        # Wait for element to be visible
        await pw_locator.wait_for(state="visible", timeout=self.action_timeout)

        match step.action_type:
            case ActionType.CLICK:
                await pw_locator.click(timeout=self.action_timeout)

            case ActionType.FILL:
                await pw_locator.fill(step.input_data or "", timeout=self.action_timeout)

            case ActionType.SELECT:
                await pw_locator.select_option(
                    step.input_data or "", timeout=self.action_timeout
                )

            case ActionType.CHECK:
                await pw_locator.check(timeout=self.action_timeout)

            case ActionType.UNCHECK:
                await pw_locator.uncheck(timeout=self.action_timeout)

            case ActionType.HOVER:
                await pw_locator.hover(timeout=self.action_timeout)

            case ActionType.NAVIGATE:
                url = step.input_data or step.page_url or ""
                if url:
                    await page.goto(url, wait_until="networkidle")

            case ActionType.WAIT:
                await page.wait_for_timeout(int(step.input_data or "2000"))

            case ActionType.ASSERT_VISIBLE:
                await pw_locator.wait_for(state="visible", timeout=self.action_timeout)

            case ActionType.ASSERT_TEXT:
                actual_text = await pw_locator.text_content()
                expected = step.expected_result
                if expected and expected.lower() not in (actual_text or "").lower():
                    raise AssertionError(
                        f"Text mismatch: expected '{expected}' in '{actual_text}'"
                    )

            case ActionType.ASSERT_VALUE:
                actual_value = await pw_locator.input_value()
                expected = step.expected_result
                if expected and expected != actual_value:
                    raise AssertionError(
                        f"Value mismatch: expected '{expected}', got '{actual_value}'"
                    )

            case ActionType.SCREENSHOT:
                pass  # Screenshots captured automatically

            case _:
                logger.warning("Unknown action type: %s", step.action_type)

    def _resolve_locator(self, page: Page, locator: Locator):
        """Convert a Locator model into a Playwright locator object."""
        from models.schemas import LocatorStrategy

        match locator.strategy:
            case LocatorStrategy.TEST_ID:
                return page.get_by_test_id(locator.value)
            case LocatorStrategy.ID:
                return page.locator(f"#{locator.value}")
            case LocatorStrategy.ARIA:
                # Try role-based first, fall back to label
                if "=" in locator.value:
                    role, name = locator.value.split("=", 1)
                    return page.get_by_role(role.strip(), name=name.strip())
                return page.get_by_label(locator.value)
            case LocatorStrategy.CSS:
                return page.locator(locator.value)
            case LocatorStrategy.XPATH:
                return page.locator(locator.value)
            case LocatorStrategy.VISUAL:
                return page.get_by_text(locator.value)
            case _:
                return page.locator(locator.value)
