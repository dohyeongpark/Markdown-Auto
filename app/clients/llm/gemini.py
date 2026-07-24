from __future__ import annotations

import httpx

from app.config import get_settings

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiClient:
    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self._model = model
        self._api_key = get_settings().llm_api_key

    async def generate_docs(self, prompt: str) -> str:
        url = f"{GEMINI_API_BASE}/{self._model}:generateContent"
        body = {"contents": [{"parts": [{"text": prompt}]}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, params={"key": self._api_key}, json=body)
        response.raise_for_status()

        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
