"""
Unified LLM client — same interface for Ollama (local) and vLLM (cloud).
Both expose an OpenAI-compatible /v1/chat/completions endpoint.
"""

import json
from typing import Any, AsyncIterator

import httpx

from app.config import settings


class LLMClient:
    def __init__(self):
        self.base_url = settings.llm_base_url.rstrip("/")
        self.http = httpx.AsyncClient(timeout=120.0)

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        response_format: dict | None = None,
        max_tokens: int = 2048,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        res = await self.http.post(
            f"{self.base_url}/chat/completions",
            json=payload,
        )
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    async def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        async with self.http.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError):
                        continue

    async def embed(self, model: str, text: str) -> list[float]:
        res = await self.http.post(
            f"{self.base_url}/embeddings",
            json={"model": model, "input": text},
        )
        res.raise_for_status()
        return res.json()["data"][0]["embedding"]

    async def chat_json(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
    ) -> dict:
        """Convenience wrapper that enforces JSON output and parses it."""
        content = await self.chat(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return json.loads(content)

    async def close(self):
        await self.http.aclose()


# Module-level singleton
_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
