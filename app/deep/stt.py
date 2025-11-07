from __future__ import annotations

import os
from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import UploadFile

ENABLE_WHISPER = os.getenv("ENABLE_WHISPER", "false").lower() in {"1", "true", "yes"}
WHISPER_PROVIDER = os.getenv("WHISPER_PROVIDER", "local")
WHISPER_MODEL_BASE = os.getenv("WHISPER_MODEL_BASE", "tiny")


async def transcribe_audio(file: UploadFile) -> Optional[str]:
    if not ENABLE_WHISPER:
        return None

    if WHISPER_PROVIDER == "openai":
        try:
            from openai import OpenAI

            client = OpenAI()
            with NamedTemporaryFile(delete=True) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp.flush()
                with open(tmp.name, "rb") as fp:
                    resp = client.audio.transcriptions.create(model="whisper-1", file=fp)
                return getattr(resp, "text", None)
        except Exception:
            return None

    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(WHISPER_MODEL_BASE, compute_type="int8")
        with NamedTemporaryFile(delete=True, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp.flush()
            segments, _ = model.transcribe(tmp.name, beam_size=1, vad_filter=True)
            text = " ".join(segment.text.strip() for segment in segments)
            return text.strip() or None
    except Exception:
        return None
