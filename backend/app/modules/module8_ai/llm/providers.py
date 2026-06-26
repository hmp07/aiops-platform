"""Unified LLM provider abstraction for multi-model support.

All Chinese LLM providers (DeepSeek, GLM, Qwen, Hunyuan) and
private deployments (vLLM, Ollama) use OpenAI-compatible APIs
at /v1/chat/completions — a single implementation covers them all.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx


@dataclass
class ChatResult:
    content: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    tool_calls: list[dict] | None = None
    finish_reason: str = "stop"
    estimated_cost: float = 0.0


class BaseLLMProvider(ABC):
    """Abstract LLM provider."""

    @abstractmethod
    async def chat(
        self, messages: list[dict], tools: list[dict] | None = None, stream: bool = False,
    ) -> ChatResult: ...

    @abstractmethod
    async def list_models(self) -> list[str]: ...

    @abstractmethod
    async def health_check(self) -> bool: ...


# ── OpenAI-compatible provider ────────────────────────────────

# Built-in presets for common Chinese LLM providers
PROVIDER_PRESETS: dict[str, dict] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "input_price": 1.0,    # ¥1 / 1M tokens
        "output_price": 2.0,   # ¥2 / 1M tokens
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
        "models": ["glm-4-plus", "glm-4-flash", "glm-4-air"],
        "input_price": 1.0,
        "output_price": 1.0,
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo"],
        "input_price": 2.0,
        "output_price": 6.0,
    },
    "openai_compatible": {
        "base_url": "http://localhost:11434/v1",  # Ollama default
        "default_model": "llama3",
        "models": [],
        "input_price": 0.0,
        "output_price": 0.0,
    },
}


class OpenAICompatibleProvider(BaseLLMProvider):
    """Provider for any OpenAI-compatible API (/v1/chat/completions).

    Covers: DeepSeek, GLM, Qwen, Hunyuan, vLLM, Ollama, etc.
    """

    def __init__(self, base_url: str, api_key: str = "",
                 default_model: str = "deepseek-chat",
                 input_price: float = 1.0, output_price: float = 2.0,
                 timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model
        self.input_price = input_price    # per 1M tokens
        self.output_price = output_price  # per 1M tokens
        self.timeout = timeout

    async def chat(
        self, messages: list[dict], tools: list[dict] | None = None, stream: bool = False,
    ) -> ChatResult:
        """Send chat completion request to OpenAI-compatible API."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body: dict = {
            "model": self.default_model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        if stream:
            body["stream"] = True

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions", json=body, headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        usage = data.get("usage", {})

        # Parse tool calls if present
        tool_calls = None
        raw_tool_calls = msg.get("tool_calls")
        if raw_tool_calls:
            tool_calls = [
                {"id": t.get("id", ""), "name": t.get("function", {}).get("name", ""),
                 "arguments": t.get("function", {}).get("arguments", "{}")}
                for t in raw_tool_calls
            ]

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost = self._estimate_cost(prompt_tokens, completion_tokens)

        return ChatResult(
            content=msg.get("content") or "",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason", "stop"),
            estimated_cost=cost,
        )

    async def list_models(self) -> list[str]:
        """Fetch available models from the API."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                data = resp.json()
                return [m.get("id", "") for m in data.get("data", [])]
        except Exception:
            return []

    async def health_check(self) -> bool:
        """Quick connectivity test."""
        try:
            result = await self.chat(
                [{"role": "user", "content": "ping"}],
                stream=False,
            )
            return bool(result.content)
        except Exception:
            return False

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (
            prompt_tokens / 1_000_000 * self.input_price
            + completion_tokens / 1_000_000 * self.output_price
        )


# ── Provider factory ──────────────────────────────────────────

def create_provider_from_config(config: dict) -> BaseLLMProvider:
    """Instantiate a provider from a ModelProvider DB record."""
    ptype = config.get("provider_type", "openai_compatible")
    preset = PROVIDER_PRESETS.get(ptype, PROVIDER_PRESETS["openai_compatible"])

    return OpenAICompatibleProvider(
        base_url=config.get("base_url", preset["base_url"]),
        api_key=config.get("api_key_encrypted", ""),
        default_model=config.get("default_model", preset["default_model"]),
        input_price=config.get("input_price", preset["input_price"]),
        output_price=config.get("output_price", preset["output_price"]),
    )
