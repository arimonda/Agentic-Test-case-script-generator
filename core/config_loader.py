"""
Configuration Loader.

Loads and merges configuration from config.yaml and .env files
into an AppConfig model for use throughout the application.
"""

import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from models.schemas import AIProvider, AppConfig

logger = logging.getLogger(__name__)


def load_config(
    config_path: str = "config/config.yaml",
    env_path: str = ".env",
) -> AppConfig:
    """
    Load application configuration from YAML + environment variables.

    Environment variables take precedence over YAML values.
    """
    # Load .env file
    env_file = Path(env_path)
    if env_file.exists():
        load_dotenv(env_file)
        logger.info("Loaded environment from: %s", env_file)

    # Load YAML config
    yaml_path = Path(config_path)
    if not yaml_path.exists():
        logger.warning("Config file not found: %s — using defaults", config_path)
        yaml_config = {}
    else:
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
        logger.info("Loaded config from: %s", yaml_path)

    # Resolve values (env > yaml > defaults)
    pw = yaml_config.get("playwright", {})
    models = yaml_config.get("models", {})
    healing = yaml_config.get("self_healing", {})
    artifacts = yaml_config.get("artifacts", {})
    rag = yaml_config.get("rag", {})
    viewport = pw.get("viewport", {})
    gemini_models = models.get("gemini", {})
    claude_models = models.get("claude", {})

    config = AppConfig(
        ai_provider=AIProvider(
            os.getenv("AI_PROVIDER", yaml_config.get("ai_provider", "CLAUDE")).upper()
        ),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        claude_api_key=os.getenv("CLAUDE_API_KEY", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        target_url=os.getenv("TARGET_URL", ""),

        # Playwright
        headless=pw.get("headless", False),
        browser=pw.get("browser", "chromium"),
        viewport_width=viewport.get("width", 1920),
        viewport_height=viewport.get("height", 1080),
        timeout=pw.get("timeout", 30000),
        navigation_timeout=pw.get("navigation_timeout", 60000),
        retries=pw.get("retries", 3),
        slow_mo=pw.get("slow_mo", 100),
        screenshot_type=pw.get("screenshot_type", "full_page"),

        # Self-healing
        self_healing_enabled=healing.get("enabled", True),
        max_healing_retries=healing.get("max_retries", 3),

        # Artifacts
        output_dir=artifacts.get("output_dir", "output"),
        generate_script=artifacts.get("generate_script", True),
        generate_docx=artifacts.get("generate_docx", True),
        generate_report=artifacts.get("generate_report", True),
        report_format=artifacts.get("report_format", "html"),

        # RAG
        rag_enabled=rag.get("enabled", True),
        chunk_size=rag.get("chunk_size", 1000),
        chunk_overlap=rag.get("chunk_overlap", 200),

        # Models
        gemini_vision_model=gemini_models.get("vision_model", "gemini-2.5-flash"),
        gemini_text_model=gemini_models.get("text_model", "gemini-2.5-flash"),
        claude_vision_model=claude_models.get("vision_model", "claude-sonnet-4-20250514"),
        claude_text_model=claude_models.get("text_model", "claude-sonnet-4-20250514"),
        model_temperature=gemini_models.get("temperature", 0.2),
        model_max_tokens=gemini_models.get("max_tokens", 4096),
    )

    logger.info("Configuration loaded: provider=%s, url=%s", config.ai_provider.value, config.target_url)
    return config
