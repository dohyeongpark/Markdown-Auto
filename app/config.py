from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    github_webhook_secret: str
    github_bot_token: str
    llm_provider: str
    llm_api_key: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        github_webhook_secret=os.environ["GITHUB_WEBHOOK_SECRET"],
        github_bot_token=os.environ["GITHUB_BOT_TOKEN"],
        llm_provider=os.environ.get("LLM_PROVIDER", "gemini"),
        llm_api_key=os.environ["LLM_API_KEY"],
    )
