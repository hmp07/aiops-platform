"""LLM Client — queries ModelProvider from DB for real LLM calls."""
import asyncio
import json
import logging
import random
from collections.abc import AsyncIterator
from typing import Any

from app.modules.module8_ai.llm.providers import OpenAICompatibleProvider, create_provider_from_config

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client that reads configuration from the database ModelProvider table.

    Falls back to demo mode when no enabled provider is found.
    """

    def __init__(self):
        self._provider: OpenAICompatibleProvider | None = None
        self._provider_loaded = False
        self._model = "demo-model"

    async def _ensure_provider(self):
        """Lazy-load the first enabled ModelProvider from DB."""
        if self._provider_loaded:
            return
        self._provider_loaded = True

        try:
            from app.core.database.session import async_session_factory
            from app.modules.module8_ai.models import ModelProvider
            from sqlalchemy import select

            async with async_session_factory() as db:
                row = (await db.execute(
                    select(ModelProvider).where(ModelProvider.is_enabled == True).limit(1)
                )).scalar_one_or_none()

                if row:
                    self._provider = create_provider_from_config({
                        "provider_type": row.provider_type,
                        "base_url": row.base_url,
                        "api_key_encrypted": row.api_key_encrypted,
                        "default_model": row.default_model,
                        "input_price": float(row.input_price or 0),
                        "output_price": float(row.output_price or 0),
                    })
                    self._model = row.default_model
                    logger.info(f"LLM Client using provider: {row.name} model={self._model}")
                else:
                    logger.info("No ModelProvider configured — using demo mode")
        except Exception as e:
            logger.warning(f"Failed to load ModelProvider: {e} — using demo mode")

    @property
    def provider(self) -> str:
        return self._provider.default_model if self._provider else "demo"

    @property
    def model(self) -> str:
        return self._model

    async def generate(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Non-streaming generation. Returns {content, tokens, cost, latency_ms}."""
        await self._ensure_provider()

        if not self._provider:
            return await self._demo_generate(messages, tools)

        start = asyncio.get_event_loop().time()

        try:
            result = await self._provider.chat(
                messages=messages,
                tools=tools,
                stream=False,
            )
            latency = int((asyncio.get_event_loop().time() - start) * 1000)
            return {
                "content": result.content,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_cost": result.estimated_cost,
                "latency_ms": latency,
            }
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return {
                "content": "[Error calling LLM provider. Check server logs for details.]",
                "prompt_tokens": 0, "completion_tokens": 0,
                "total_cost": 0.0, "latency_ms": 0,
            }

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> AsyncIterator[str]:
        """Streaming generation. Yields SSE-formatted JSON strings."""
        await self._ensure_provider()

        if not self._provider:
            async for chunk in self._demo_stream(messages, tools):
                yield chunk
            return

        # Reuse non-streaming for simplicity; streaming can be added later
        result = await self.generate(messages, tools, max_tokens, temperature)
        for word in result["content"].split():
            yield json.dumps({"type": "text_delta", "content": word + " "})
            await asyncio.sleep(0.01)

    # ── Demo fallback ──────────────────────────────────────

    async def _demo_generate(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict[str, Any]:
        last_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "no input")
        latency = random.randint(150, 400)
        if tools:
            tool_name = tools[0].get("name", "unknown") if tools else "unknown"
            return {
                "content": f"[DEMO] Would call tool '{tool_name}' for: {last_msg[:50]}...",
                "prompt_tokens": len(last_msg) // 4, "completion_tokens": 80,
                "total_cost": 0.0, "latency_ms": latency,
            }
        return {
            "content": f"[DEMO] You asked: '{last_msg[:100]}'. This is a demo response. "
                       f"In production, the AI agent will use the configured model provider.",
            "prompt_tokens": len(last_msg) // 4, "completion_tokens": 50,
            "total_cost": 0.0, "latency_ms": latency,
        }

    async def _demo_stream(self, messages: list[dict], tools: list[dict] | None = None):
        last_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "no input")
        words = f"[DEMO] '{last_msg[:80]}'. Demo streaming response. "
        for word in words.split():
            yield json.dumps({"type": "text_delta", "content": word + " "})
            await asyncio.sleep(0.03)
