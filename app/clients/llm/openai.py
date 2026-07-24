from __future__ import annotations

import httpx

from app.config import get_settings

OPENAI_API_BASE = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4.1-mini"


class OpenAIClient:
    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self._model = model
        self._api_key = get_settings().llm_api_key

    async def generate_docs(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        body = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OPENAI_API_BASE, headers=headers, json=body)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]
