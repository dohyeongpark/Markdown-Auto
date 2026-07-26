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
        headers = {"x-goog-api-key": self._api_key}
        body = {"contents": [{"parts": [{"text": prompt}]}]}

        # 키를 쿼리 파라미터(?key=...)로 보내면 httpx가 에러 시 요청 URL을 그대로
        # 예외 메시지에 실어 로그에 평문으로 남긴다. 헤더로 보내 이를 방지한다.
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=body)
        response.raise_for_status()

        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
