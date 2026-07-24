from __future__ import annotations

import httpx

from app.config import get_settings

ANTHROPIC_API_BASE = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-5"


class ClaudeClient:
    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self._model = model
        self._api_key = get_settings().llm_api_key

    async def generate_docs(self, prompt: str) -> str:
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        body = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(ANTHROPIC_API_BASE, headers=headers, json=body)
        response.raise_for_status()

        data = response.json()
        return "".join(block["text"] for block in data["content"] if block["type"] == "text")
