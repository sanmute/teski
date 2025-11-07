from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FeedbackSettings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model_mini: str = os.getenv("OPENAI_MINI_MODEL", "gpt-4.1-mini")
    openai_model_pro: str = os.getenv("OPENAI_PRO_MODEL", "gpt-4.1")

    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model_mini: str = os.getenv("ANTHROPIC_MINI_MODEL", "claude-3-5-haiku-20241022")
    anthropic_model_pro: str = os.getenv("ANTHROPIC_PRO_MODEL", "claude-3-5-sonnet-20241022")

    local_llm_base_url: str = os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8001")

    request_timeout_s: float = float(os.getenv("LLM_TIMEOUT_S", "30"))
    max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    backoff_base_s: float = float(os.getenv("LLM_BACKOFF_S", "0.6"))


def get_feedback_settings() -> FeedbackSettings:
    return FeedbackSettings()
