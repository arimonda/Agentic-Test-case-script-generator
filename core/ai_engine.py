"""
Multi-Model AI Inference Engine.

Provides a unified interface to send prompts (text + images) to
either Google Gemini or Anthropic Claude, based on configuration.
"""

import json
import logging
import time
from typing import Optional

import anthropic
import google.generativeai as genai

from models.schemas import AIProvider, AIRequest, AIResponse, AppConfig

logger = logging.getLogger(__name__)


class AIEngine:
    """
    Unified AI engine that dispatches to Gemini or Claude
    based on the configured provider.
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self._init_providers()

    def _init_providers(self) -> None:
        """Initialize API clients for configured providers."""
        if self.config.gemini_api_key:
            genai.configure(api_key=self.config.gemini_api_key)
            logger.info("Gemini API initialized")

        if self.config.claude_api_key:
            self._claude_client = anthropic.Anthropic(
                api_key=self.config.claude_api_key
            )
            logger.info("Claude API initialized")
        else:
            self._claude_client = None

    def infer(
        self,
        prompt: str,
        images: list[str] | None = None,
        provider: AIProvider | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIResponse:
        """
        Send a prompt (with optional base64 images) to the AI model.

        Parameters
        ----------
        prompt : str
            The text prompt.
        images : list[str], optional
            List of base64-encoded images to include.
        provider : AIProvider, optional
            Override the default provider from config.
        temperature : float, optional
            Override default temperature.
        max_tokens : int, optional
            Override default max tokens.

        Returns
        -------
        AIResponse with the model's text output and usage metadata.
        """
        active_provider = provider or self.config.ai_provider
        temp = temperature if temperature is not None else self.config.model_temperature
        tokens = max_tokens or self.config.model_max_tokens
        imgs = images or []

        request = AIRequest(
            provider=active_provider,
            model=self._get_model_name(active_provider, has_images=bool(imgs)),
            prompt=prompt,
            images=imgs,
            temperature=temp,
            max_tokens=tokens,
        )

        logger.info(
            "AI inference: provider=%s model=%s images=%d prompt_len=%d",
            request.provider,
            request.model,
            len(request.images),
            len(request.prompt),
        )

        start = time.perf_counter()
        if active_provider == AIProvider.GEMINI:
            response = self._infer_gemini(request)
        elif active_provider == AIProvider.CLAUDE:
            response = self._infer_claude(request)
        else:
            raise ValueError(f"Unsupported provider: {active_provider}")

        response.latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "AI response: %d chars in %.0f ms | usage=%s",
            len(response.content),
            response.latency_ms,
            response.usage,
        )
        return response

    # --------------------------------------------------------------------- #
    # Provider-Specific Implementations
    # --------------------------------------------------------------------- #

    def _infer_gemini(self, request: AIRequest) -> AIResponse:
        """Call Google Gemini (supports native multimodal)."""
        import base64

        model = genai.GenerativeModel(request.model)

        parts = []
        for img_b64 in request.images:
            img_bytes = base64.b64decode(img_b64)
            parts.append({
                "mime_type": "image/jpeg",
                "data": img_bytes,
            })
        parts.append(request.prompt)

        generation_config = genai.types.GenerationConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        )

        response = model.generate_content(
            parts,
            generation_config=generation_config,
        )

        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
            }

        return AIResponse(
            provider=AIProvider.GEMINI,
            model=request.model,
            content=response.text,
            usage=usage,
        )

    def _infer_claude(self, request: AIRequest) -> AIResponse:
        """Call Anthropic Claude (supports vision via base64 images)."""
        if not self._claude_client:
            raise RuntimeError("Claude API key not configured")

        content_blocks: list[dict] = []

        for img_b64 in request.images:
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": img_b64,
                },
            })

        content_blocks.append({"type": "text", "text": request.prompt})

        response = self._claude_client.messages.create(
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": content_blocks}],
        )

        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }

        return AIResponse(
            provider=AIProvider.CLAUDE,
            model=request.model,
            content=response.content[0].text,
            usage=usage,
            raw_response=response,
        )

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #

    def _get_model_name(self, provider: AIProvider, has_images: bool) -> str:
        """Return the appropriate model name based on provider and task type."""
        if provider == AIProvider.GEMINI:
            return self.config.gemini_vision_model if has_images else self.config.gemini_text_model
        elif provider == AIProvider.CLAUDE:
            return self.config.claude_vision_model if has_images else self.config.claude_text_model
        raise ValueError(f"Unknown provider: {provider}")

    def infer_json(
        self,
        prompt: str,
        images: list[str] | None = None,
        provider: AIProvider | None = None,
    ) -> dict:
        """
        Convenience method: infer and parse the result as JSON.
        Strips markdown code fences if present.
        """
        response = self.infer(prompt, images, provider)
        text = response.content.strip()

        # Strip markdown JSON fences
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        return json.loads(text)
