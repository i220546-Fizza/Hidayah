"""
Model providers behind small interfaces, so the pipeline can be tested without any network
and the real provider can be swapped without touching the pipeline.

* LLM: Claude (Anthropic Messages API over HTTPS). The key is read from the environment.
* Embeddings: no provider is chosen yet. Claude has no embeddings endpoint, so the project owner
  must pick one (it must produce 1024-dimension vectors). Until then retrieval is keyword-only.
"""
from typing import Protocol

import httpx

from app.core.config import get_settings


class LLMError(Exception):
    pass


class LLM(Protocol):
    def complete(self, system: str, user: str, max_tokens: int = 900) -> str: ...


class Embedder(Protocol):
    model_name: str
    index_version: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class AnthropicLLM:
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str) -> None:
        self._key, self._model = api_key, model

    def complete(self, system: str, user: str, max_tokens: int = 900) -> str:
        try:
            r = httpx.post(
                self.URL,
                headers={"x-api-key": self._key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": self._model, "max_tokens": max_tokens, "temperature": 0, "system": system,
                      "messages": [{"role": "user", "content": user}]},
                timeout=60,
            )
            r.raise_for_status()
            parts = r.json().get("content", [])
            return "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMError("The answer service is unavailable.") from exc


def get_llm() -> LLM | None:
    """None when no key is configured; the API then says so honestly instead of pretending."""
    s = get_settings()
    return AnthropicLLM(s.anthropic_api_key, s.anthropic_model) if s.anthropic_api_key else None


def get_embedder() -> Embedder | None:
    return None
