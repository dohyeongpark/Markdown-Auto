from __future__ import annotations

from typing import Protocol

from app.config import get_settings


class LLMClient(Protocol):
    """모든 LLM Provider가 구현해야 하는 인터페이스.

    Gemini -> Claude 등 Provider 교체는 get_llm_client()의 분기 하나로 끝나야 한다.
    벤더 SDK/httpx 호출은 app/clients/llm/*.py 안에서만 하고, 이 모듈 밖에서
    벤더별 클라이언트를 직접 import하지 않는다.
    """

    async def generate_docs(self, prompt: str) -> str: ...


def get_llm_client() -> LLMClient:
    provider = get_settings().llm_provider

    if provider == "gemini":
        from app.clients.llm.gemini import GeminiClient

        return GeminiClient()
    if provider == "claude":
        from app.clients.llm.claude import ClaudeClient

        return ClaudeClient()
    if provider == "openai":
        from app.clients.llm.openai import OpenAIClient

        return OpenAIClient()

    raise ValueError(f"지원하지 않는 LLM_PROVIDER: {provider}")
