from __future__ import annotations

import asyncio
from typing import Tuple

import httpx
import tiktoken
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from ..config_feedback import get_feedback_settings

settings = get_feedback_settings()


def count_tokens_estimate(text: str, model_hint: str = "gpt-4o-mini") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model_hint)
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
    try:
        return len(encoding.encode(text))
    except Exception:
        return max(1, int(len(text) / 4))


async def _with_retries(coro_fn, *args, **kwargs):
    attempts = settings.max_retries
    for attempt in range(attempts + 1):
        try:
            return await coro_fn(*args, **kwargs)
        except Exception:
            if attempt >= attempts:
                raise
            await asyncio.sleep(settings.backoff_base_s * (2**attempt))


_openai_client: AsyncOpenAI | None = None


def _get_openai() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout_s)
    return _openai_client


async def call_openai_gpt(model: str, prompt: str) -> Tuple[str, int]:
    client = _get_openai()

    async def _call():
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are Teski, a concise learning coach. 2–4 sentences max."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=220,
        )
        text = (resp.choices[0].message.content or "").strip()
        usage = getattr(resp, "usage", None)
        completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
        tokens_out = completion_tokens or count_tokens_estimate(text, model)
        return text, tokens_out

    return await _with_retries(_call)


_anthropic_client: AsyncAnthropic | None = None


def _get_anthropic() -> AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=settings.request_timeout_s)
    return _anthropic_client


async def call_anthropic(model: str, prompt: str) -> Tuple[str, int]:
    client = _get_anthropic()

    async def _call():
        resp = await client.messages.create(
            model=model,
            max_tokens=220,
            temperature=0.3,
            system="You are Teski, a concise learning coach. 2–4 sentences max.",
            messages=[{"role": "user", "content": prompt}],
        )
        pieces = [block.text for block in resp.content if getattr(block, "type", "") == "text"]
        text = "".join(pieces).strip()
        usage = getattr(resp, "usage", None)
        output_tokens = getattr(usage, "output_tokens", None) if usage else None
        tokens_out = output_tokens or count_tokens_estimate(text, model)
        return text, tokens_out

    return await _with_retries(_call)


async def call_local_llama(model: str, prompt: str) -> Tuple[str, int]:
    url = settings.local_llm_base_url.rstrip("/") + "/generate"

    async def _call():
        async with httpx.AsyncClient(timeout=settings.request_timeout_s) as client:
            resp = await client.post(
                url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "max_new_tokens": 220,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            payload = resp.json()
            text = (payload.get("text") or "").strip()
            tokens_out = count_tokens_estimate(text, "llama-3.1-70b")
            return text, tokens_out

    return await _with_retries(_call)
