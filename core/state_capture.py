"""
Page State Capture Engine.

Uses Playwright to capture the full-page screenshot, DOM content,
and visible text for a given browser page. This state is then sent
to the AI engine for analysis.
"""

import logging
from datetime import datetime
from pathlib import Path

from playwright.async_api import Page

from models.schemas import PageState
from utils.dom_utils import extract_visible_text, minify_html
from utils.screenshot_utils import prepare_for_ai, save_screenshot

logger = logging.getLogger(__name__)


class StateCaptureEngine:
    """Captures and packages the current state of a Playwright page."""

    def __init__(self, output_dir: str = "output/screenshots"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    async def capture(
        self,
        page: Page,
        step_label: str = "page",
        full_page: bool = True,
    ) -> PageState:
        """
        Capture a complete snapshot of the current page.

        Returns a PageState containing the screenshot path, base64
        encoding, raw HTML, minified HTML, and visible text.
        """
        logger.info("Capturing page state: %s (%s)", page.url, step_label)

        # Wait for network idle to ensure page is fully loaded
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            logger.warning("Network idle timeout — proceeding with current state")

        # Screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{step_label}_{timestamp}.png"
        screenshot_bytes = await page.screenshot(full_page=full_page)
        screenshot_path = save_screenshot(screenshot_bytes, self.output_dir, filename)
        screenshot_b64 = prepare_for_ai(screenshot_bytes)

        # DOM
        dom_html = await page.content()
        minified = minify_html(dom_html)
        visible_text = extract_visible_text(dom_html)

        state = PageState(
            url=page.url,
            title=await page.title(),
            screenshot_path=screenshot_path,
            screenshot_base64=screenshot_b64,
            dom_html=dom_html,
            minified_html=minified,
            visible_text=visible_text,
        )

        logger.info(
            "State captured: %s | DOM %d chars | Minified %d chars",
            screenshot_path,
            len(dom_html),
            len(minified),
        )
        return state

    async def capture_element(
        self,
        page: Page,
        selector: str,
        label: str = "element",
    ) -> bytes | None:
        """Capture a screenshot of a single element, if it exists."""
        try:
            element = page.locator(selector)
            if await element.count() > 0:
                return await element.first.screenshot()
        except Exception as exc:
            logger.warning("Could not capture element '%s': %s", selector, exc)
        return None
