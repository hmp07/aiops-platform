"""LLM Client — Anthropic / OpenAI / Demo multi-provider with streaming."""
import asyncio
import json
import logging
import random
from collections.abc import AsyncIterator
from typing import Any

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMClient:
    """Multi-provider LLM client.

    Three modes:
      - anthropic: Claude models (via Anthropic SDK)
      - openai:    GPT models (via OpenAI SDK)
      - demo:      No API key needed, returns mock/echo responses
    """

    def __init__(self, settings_override=None):
        cfg = settings_override or settings
        self._provider = cfg.LLM_PROVIDER or "demo"
        self._client = None

        if self._provider == "anthropic" and cfg.ANTHROPIC_API_KEY:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=cfg.ANTHROPIC_API_KEY)
                self._model = cfg.ANTHROPIC_MODEL
            except ImportError:
                logger.warning("anthropic SDK not installed, falling back to demo mode")
                self._provider = "demo"
        elif self._provider == "openai" and cfg.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=cfg.OPENAI_API_KEY)
                self._model = cfg.OPENAI_MODEL
            except ImportError:
                logger.warning("openai SDK not installed, falling back to demo mode")
                self._provider = "demo"
        else:
            self._provider = "demo"

        logger.info(f"LLM Client initialized: provider={self._provider}")

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        if self._provider == "anthropic":
            return settings.ANTHROPIC_MODEL
        elif self._provider == "openai":
            return settings.OPENAI_MODEL
        return "demo-model"

    async def generate(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Non-streaming generation. Returns {content, tokens, cost, latency_ms}."""

        if self._provider == "demo":
            return await self._demo_generate(messages, tools)

        start = asyncio.get_event_loop().time()

        if self._provider == "anthropic":
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                tools=tools or [],
            )
            latency = int((asyncio.get_event_loop().time() - start) * 1000)
            content = response.content[0].text if response.content else ""
            return {
                "content": content,
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_cost": self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens),
                "latency_ms": latency,
            }

        elif self._provider == "openai":
            response = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                tools=tools or [],
            )
            latency = int((asyncio.get_event_loop().time() - start) * 1000)
            choice = response.choices[0]
            return {
                "content": choice.message.content or "",
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_cost": self._estimate_cost(response.usage.prompt_tokens, response.usage.completion_tokens),
                "latency_ms": latency,
            }

        return {"content": "No provider configured", "prompt_tokens": 0, "completion_tokens": 0, "total_cost": 0.0, "latency_ms": 0}

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> AsyncIterator[str]:
        """Streaming generation. Yields SSE-formatted JSON strings."""

        if self._provider == "demo":
            async for chunk in self._demo_stream(messages, tools):
                yield chunk
            return

        start = asyncio.get_event_loop().time()

        if self._provider == "anthropic":
            async with self._client.messages.stream(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                tools=tools or [],
            ) as stream:
                async for text in stream.text_stream:
                    yield json.dumps({"type": "text_delta", "content": text})

        elif self._provider == "openai":
            stream = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                tools=tools or [],
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield json.dumps({"type": "text_delta", "content": chunk.choices[0].delta.content})

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Rough cost estimation. Updated with latest pricing."""
        if self._provider == "anthropic":
            # Claude Sonnet 4: $3/$15 per MTok
            return (prompt_tokens * 3 + completion_tokens * 15) / 1_000_000
        elif self._provider == "openai":
            # GPT-4o: $2.5/$10 per MTok
            return (prompt_tokens * 2.5 + completion_tokens * 10) / 1_000_000
        return 0.0

    # ---- Demo mode ----
    async def _demo_generate(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        """Mock generation that echoes the last user message."""
        last_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "no input")
        latency = random.randint(150, 400)

        # If tools are provided, generate a mock tool call response
        if tools:
            tool_name = tools[0].get("name", "unknown") if tools else "unknown"
            return {
                "content": f"[DEMO] Would call tool '{tool_name}' to answer your question about: {last_msg[:50]}...",
                "prompt_tokens": len(last_msg) // 4,
                "completion_tokens": 80,
                "total_cost": 0.0,
                "latency_ms": latency,
            }

        return {
            "content": f"[DEMO RESPONSE] You asked: '{last_msg[:100]}'. "
                       f"This is a demo response. In production, "
                       f"the AI agent would analyze your query using the available tools "
                       f"and provide a structured answer with citations and evidence.",
            "prompt_tokens": len(last_msg) // 4,
            "completion_tokens": 50,
            "total_cost": 0.0,
            "latency_ms": latency,
        }

    async def _demo_stream(self, messages: list[dict], tools: list[dict] | None = None):
        """Mock streaming that yields words one at a time."""
        last_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "no input")
        words = f"[DEMO] Analyzing your query: '{last_msg[:80]}'. "
        words += "This is a demo streaming response. In production, the AI agent would "
        words += "perform tool calls and provide a structured answer."
        for word in words.split():
            yield json.dumps({"type": "text_delta", "content": word + " "})
            await asyncio.sleep(0.03)
