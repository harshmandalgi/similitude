"""One client for every OpenAI-compatible provider, with prices and a hard spending cap.

A model is named "provider:model", e.g. "openai:gpt-5.4-nano" or "xai:grok-4.20-0309-non-reasoning".
Every call is priced from the provider's own token counts and charged to a Ledger, which refuses
new calls once the cap is reached.
"""

from __future__ import annotations

import json
import os
import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ENV_FILE = Path.home() / "Desktop" / "projects" / ".env"

PROVIDERS = {
    "openai": (None, "OPENAI_API_KEY"),
    "xai": ("https://api.x.ai/v1", "XAI_API_KEY"),
    "deepseek": ("https://api.deepseek.com", "DEEPSEEK_API_KEY"),
}


@dataclass(frozen=True)
class Price:
    """US dollars per million tokens."""

    input: float
    cached: float
    output: float


# Checked 2026-10-14: OpenAI's pricing page; xAI's /v1/language-models endpoint.
PRICES = {
    "openai:gpt-5.4-nano": Price(0.20, 0.02, 1.25),
    "openai:gpt-5.4-mini": Price(0.75, 0.075, 4.50),
    "openai:gpt-5.4": Price(2.50, 0.25, 15.00),
    "openai:gpt-5-nano": Price(0.05, 0.005, 0.40),
    "openai:gpt-5-mini": Price(0.25, 0.025, 2.00),
    "openai:gpt-4.1-nano": Price(0.10, 0.025, 0.40),
    "openai:gpt-4.1-mini": Price(0.40, 0.10, 1.60),
    "xai:grok-4.20-0309-non-reasoning": Price(1.25, 0.20, 2.50),
    "xai:grok-4.3": Price(1.25, 0.20, 2.50),
}


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class Usage:
    input: int = 0  # all prompt tokens, cached included
    cached: int = 0
    output: int = 0  # reasoning included

    def cost(self, price: Price) -> float:
        fresh = max(self.input - self.cached, 0)
        return (fresh * price.input + self.cached * price.cached + self.output * price.output) / 1e6


@dataclass
class Completion:
    model: str
    text: str
    tool_calls: list[dict[str, Any]]  # [{"id", "name", "arguments": dict}]
    message: dict[str, Any]  # the assistant message, ready to append to the conversation
    usage: Usage
    cost_usd: float
    latency_s: float

    def to_json(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "text": self.text,
            "tool_calls": self.tool_calls,
            "message": self.message,
            "usage": self.usage.__dict__,
            "cost_usd": self.cost_usd,
            "latency_s": self.latency_s,
        }

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> Completion:
        return cls(
            model=d["model"],
            text=d["text"],
            tool_calls=d["tool_calls"],
            message=d["message"],
            usage=Usage(**d["usage"]),
            cost_usd=d["cost_usd"],
            latency_s=d["latency_s"],
        )


@dataclass
class Ledger:
    """Running total of real spend. Saved to disk so the cap holds across runs."""

    cap_usd: float
    path: Path | None = None
    spent_usd: float = 0.0
    by_tag: dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        if self.path and self.path.exists():
            saved = json.loads(self.path.read_text())
            self.spent_usd = saved["spent_usd"]
            self.by_tag = saved["by_tag"]

    def check(self) -> None:
        if self.spent_usd >= self.cap_usd:
            raise BudgetExceeded(f"spent ${self.spent_usd:.4f} of the ${self.cap_usd:.2f} cap")

    def charge(self, usd: float, tag: str) -> None:
        with self._lock:
            self.spent_usd += usd
            self.by_tag[tag] = self.by_tag.get(tag, 0.0) + usd
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(
                    json.dumps({"spent_usd": self.spent_usd, "by_tag": self.by_tag}, indent=1)
                )


def load_env() -> dict[str, str]:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env[key] = value.strip().strip('"').strip("'")
    return {**env, **{k: v for k, v in os.environ.items() if k in env}}


class LLMClient:
    """Thin wrapper over the openai SDK. Retries rate limits and server errors."""

    def __init__(self, ledger: Ledger, *, max_retries: int = 6) -> None:
        from openai import OpenAI

        self.ledger = ledger
        self.max_retries = max_retries
        env = load_env()
        self._clients = {}
        for provider, (base_url, key_name) in PROVIDERS.items():
            if env.get(key_name):
                self._clients[provider] = OpenAI(api_key=env[key_name], base_url=base_url)

    def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 2000,
        json_mode: bool = False,
        tool_choice: str | None = None,
        tag: str = "",
    ) -> Completion:
        provider, name = model.split(":", 1)
        if model not in PRICES:
            raise KeyError(f"no price for {model}; add it to PRICES before spending")
        client = self._clients[provider]
        self.ledger.check()
        kwargs: dict[str, Any] = {"model": name, "messages": messages}
        if provider == "openai":
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        from openai import APIConnectionError, APIStatusError, RateLimitError

        for attempt in range(self.max_retries):
            start = time.perf_counter()
            try:
                response = client.chat.completions.create(**kwargs)
                break
            except (RateLimitError, APIConnectionError) as exc:
                error = exc
            except APIStatusError as exc:
                if exc.status_code < 500:
                    raise
                error = exc
            time.sleep(min(60, 2**attempt + random.random()))
        else:
            raise RuntimeError(f"{model}: gave up after {self.max_retries} attempts: {error}")
        latency = time.perf_counter() - start

        choice = response.choices[0].message
        usage = Usage(
            input=response.usage.prompt_tokens,
            cached=getattr(response.usage.prompt_tokens_details, "cached_tokens", 0) or 0,
            output=response.usage.completion_tokens,
        )
        cost = usage.cost(PRICES[model])
        self.ledger.charge(cost, tag or model)

        tool_calls = []
        raw_calls = []
        for call in choice.tool_calls or []:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {"_unparsed": call.function.arguments}
            tool_calls.append({"id": call.id, "name": call.function.name, "arguments": arguments})
            raw_calls.append(
                {
                    "id": call.id,
                    "type": "function",
                    "function": {"name": call.function.name, "arguments": call.function.arguments},
                }
            )
        message: dict[str, Any] = {"role": "assistant", "content": choice.content or ""}
        if raw_calls:
            message["tool_calls"] = raw_calls
        return Completion(model, choice.content or "", tool_calls, message, usage, cost, latency)
