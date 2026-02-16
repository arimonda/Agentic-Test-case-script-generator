"""
AI-Driven Locator Identification Engine.

Sends the page screenshot + minified DOM to the AI model and receives
a ranked set of Playwright locators for each target element.
"""

import json
import logging
from typing import Optional

from core.ai_engine import AIEngine
from models.schemas import (
    AIProvider,
    Locator,
    LocatorSet,
    LocatorStrategy,
    PageState,
    TestStepInput,
)

logger = logging.getLogger(__name__)

LOCATOR_PROMPT_TEMPLATE = """You are an expert Playwright test automation engineer.

## Task
Analyze the provided screenshot and HTML to identify the UI element described below.
Return a JSON object with **three** Playwright locator strategies ranked by reliability.

## Target Element
- **Intent:** {intent}
- **Action:** {action_type}
- **Input Data:** {input_data}

## Page Context
- **URL:** {url}
- **Title:** {title}

## HTML (minified, interactive elements emphasized)
```html
{html_snippet}
```

## Instructions
1. Study the screenshot to visually locate the element.
2. Cross-reference with the HTML to find the best locators.
3. Return ONLY valid JSON (no markdown fences) in this exact structure:

{{
    "element_name": "<human-readable name>",
    "element_description": "<what this element is>",
    "primary": {{
        "strategy": "<test_id|id|aria|css|xpath|visual>",
        "value": "<locator value>",
        "confidence": <0.0-1.0>,
        "description": "<why this is the best choice>"
    }},
    "secondary": {{
        "strategy": "<test_id|id|aria|css|xpath|visual>",
        "value": "<locator value>",
        "confidence": <0.0-1.0>,
        "description": "<backup rationale>"
    }},
    "tertiary": {{
        "strategy": "<test_id|id|aria|css|xpath|visual>",
        "value": "<locator value>",
        "confidence": <0.0-1.0>,
        "description": "<last-resort rationale>"
    }}
}}

Prioritize: data-testid > id > aria-label > CSS > XPath > visual text.
"""


class LocatorEngine:
    """Uses AI vision + DOM analysis to produce ranked locator sets."""

    def __init__(self, ai_engine: AIEngine):
        self.ai = ai_engine

    def identify_locators(
        self,
        page_state: PageState,
        step: TestStepInput,
        provider: AIProvider | None = None,
    ) -> LocatorSet:
        """
        Given the current page state and a test step, ask the AI
        to identify the target element and return ranked locators.
        """
        prompt = LOCATOR_PROMPT_TEMPLATE.format(
            intent=step.intent,
            action_type=step.action_type.value,
            input_data=step.input_data or "N/A",
            url=page_state.url,
            title=page_state.title,
            html_snippet=page_state.minified_html[:15000],
        )

        images = []
        if page_state.screenshot_base64:
            images.append(page_state.screenshot_base64)

        logger.info("Requesting locators for: %s", step.intent)

        try:
            data = self.ai.infer_json(prompt, images=images, provider=provider)
            return self._parse_locator_response(data)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse AI locator response: %s", exc)
            return self._fallback_locator(step)
        except Exception as exc:
            logger.error("Locator identification failed: %s", exc)
            return self._fallback_locator(step)

    def identify_multiple_locators(
        self,
        page_state: PageState,
        steps: list[TestStepInput],
    ) -> list[LocatorSet]:
        """Identify locators for multiple steps on the same page."""
        results = []
        for step in steps:
            locator_set = self.identify_locators(page_state, step)
            results.append(locator_set)
        return results

    def _parse_locator_response(self, data: dict) -> LocatorSet:
        """Parse the AI JSON response into a LocatorSet model."""
        def _parse_locator(loc_data: dict) -> Locator:
            return Locator(
                strategy=LocatorStrategy(loc_data["strategy"]),
                value=loc_data["value"],
                confidence=float(loc_data.get("confidence", 0.5)),
                description=loc_data.get("description", ""),
            )

        primary = _parse_locator(data["primary"])
        secondary = _parse_locator(data["secondary"]) if data.get("secondary") else None
        tertiary = _parse_locator(data["tertiary"]) if data.get("tertiary") else None

        return LocatorSet(
            element_name=data.get("element_name", "unknown"),
            element_description=data.get("element_description", ""),
            primary=primary,
            secondary=secondary,
            tertiary=tertiary,
        )

    def _fallback_locator(self, step: TestStepInput) -> LocatorSet:
        """Produce a best-effort locator from the step intent alone."""
        logger.warning("Using fallback locator for: %s", step.intent)
        return LocatorSet(
            element_name=step.intent,
            element_description="Fallback — AI identification failed",
            primary=Locator(
                strategy=LocatorStrategy.VISUAL,
                value=step.intent,
                confidence=0.3,
                description="Fallback text-based locator",
            ),
        )
