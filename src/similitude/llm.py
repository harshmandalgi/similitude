"""One client for every OpenAI-compatible provider, with prices and a hard spending cap.

A model is named "provider:model", e.g. "vertex:google/gemini-3.5-flash-lite" or
"openai:gpt-5.4-nano". Vertex is Gemini on Google Cloud through its OpenAI-compatible endpoint,
authenticated with Application Default Credentials (`gcloud auth application-default login`).
Every call is priced from the provider's own token counts and list prices and charged to a
Ledger, which refuses new calls (and retries) once the cap is reached. Calls already in flight
when the cap is reached still finish, so the total can go over the cap by up to one call per
worker.
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

# API keys and settings: a .env file in the repo root, or the file that $SIMILITUDE_ENV_FILE names.
ROOT = Path(__file__).resolve().parents[2]
# Settings read from the environment even when no .env file names them.
ENV_KEYS = ("OPENAI_API_KEY", "XAI_API_KEY", "GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION")

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
    # Gemini on Vertex. Flash-Lite: Google's pricing page, 2026-10-14. 3.8 Flash: a deliberately
    # high rate (Google lists $0.75/$3.75 as an introductory rate), so the cap holds.
    "vertex:google/gemini-3.5-flash-lite": Price(0.30, 0.03, 2.50),
    "vertex:google/gemini-3.1-flash-lite": Price(0.25, 0.025, 1.50),
    "vertex:google/gemini-3.8-flash": Price(1.50, 0.15, 7.50),
}

# Per-model request settings. Gemini 3.8 Flash thinks by default; "low" turns it off (probed
# 2026-10-14). The Flash-Lite models do not think unless asked, so they get nothing.
MODEL_PARAMS: dict[str, dict[str, Any]] = {
    "vertex:google/gemini-3.8-flash": {"reasoning_effort": "low"},
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
    """Running total of real spend, shared by every process through one file.

    Each charge is a locked read-add-write, so parallel runs never overwrite each other's
    spend, and the cap holds across all of them."""

    cap_usd: float
    path: Path | None = None
    spent_usd: float = 0.0
    by_tag: dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        if self.path and self.path.exists():
            saved = json.loads(self.path.read_text() or "{}")
            self.spent_usd = saved.get("spent_usd", 0.0)
            self.by_tag = saved.get("by_tag", {})

    def check(self) -> None:
        with self._lock:
            self._refresh()
            if self.spent_usd >= self.cap_usd:
                raise BudgetExceeded(f"spent ${self.spent_usd:.4f} of the ${self.cap_usd:.2f} cap")

    def charge(self, usd: float, tag: str) -> None:
        with self._lock:
            if not self.path:
                self.spent_usd += usd
                self.by_tag[tag] = self.by_tag.get(tag, 0.0) + usd
                return
            import fcntl

            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path.with_suffix(".lock"), "w") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                self._refresh()
                self.spent_usd += usd
                self.by_tag[tag] = self.by_tag.get(tag, 0.0) + usd
                tmp = self.path.with_suffix(".tmp")
                tmp.write_text(json.dumps({"spent_usd": self.spent_usd, "by_tag": self.by_tag}))
                tmp.replace(self.path)


def env_file() -> Path:
    return Path(os.environ.get("SIMILITUDE_ENV_FILE") or ROOT / ".env")


def load_env() -> dict[str, str]:
    """Keys from the .env file; a variable set in the environment wins over the file."""
    env = {}
    path = env_file()
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
    return {**env, **{k: v for k, v in os.environ.items() if k in env or k in ENV_KEYS}}


class _Vertex:
    """An OpenAI client for Vertex whose bearer token is refreshed before it goes stale."""

    SCOPE = "https://www.googleapis.com/auth/cloud-platform"

    def __init__(self, project: str, location: str = "global") -> None:
        host = "aiplatform.googleapis.com" if location == "global" else (
            f"{location}-aiplatform.googleapis.com"
        )  # fmt: skip
        self.base_url = (
            f"https://{host}/v1beta1/projects/{project}/locations/{location}/endpoints/openapi"
        )
        self._lock = threading.Lock()
        self._credentials = None
        self._client = None

    def client(self):
        import google.auth
        import google.auth.transport.requests
        from openai import OpenAI

        with self._lock:
            if self._credentials is None:
                self._credentials, _ = google.auth.default(scopes=[self.SCOPE])
            if not self._credentials.valid or self._client is None:
                self._credentials.refresh(google.auth.transport.requests.Request())
                self._client = OpenAI(
                    api_key=self._credentials.token, base_url=self.base_url, timeout=120
                )
            return self._client

    def expire(self) -> None:
        """Force a fresh token on the next call (after a 401 from a token gone stale mid-run)."""
        with self._lock:
            self._client = None


def _usage_cost(response, provider: str, model: str) -> tuple[Usage, float]:
    """Token counts and cost of one reply, from the provider's own counts."""
    u = response.usage
    if u is None:  # an empty reply may carry no usage either
        from types import SimpleNamespace

        u = SimpleNamespace(prompt_tokens=0, completion_tokens=0, prompt_tokens_details=None)
    output = u.completion_tokens or 0  # Vertex sometimes leaves counts out
    if provider == "vertex":  # Vertex leaves thinking out of completion_tokens, bills it
        details = getattr(u, "completion_tokens_details", None)
        output += (getattr(details, "reasoning_tokens", 0) or 0) if details else 0
    usage = Usage(
        input=u.prompt_tokens or 0,
        cached=getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) or 0,
        output=output,
    )
    return usage, usage.cost(PRICES[model])


class LLMClient:
    """Thin wrapper over the openai SDK. Retries rate limits and server errors."""

    def __init__(self, ledger: Ledger, *, max_retries: int = 12) -> None:
        from openai import OpenAI

        self.ledger = ledger
        self.max_retries = max_retries
        self.retries = 0  # rate-limit and server-error retries so far, for progress logs
        env = load_env()
        self._clients = {}
        for provider, (base_url, key_name) in PROVIDERS.items():
            if env.get(key_name):
                self._clients[provider] = OpenAI(
                    api_key=env[key_name], base_url=base_url, timeout=120
                )
        self._vertex = (
            _Vertex(env["GOOGLE_CLOUD_PROJECT"], env.get("GOOGLE_CLOUD_LOCATION") or "global")
            if env.get("GOOGLE_CLOUD_PROJECT")
            else None
        )

    def _client_for(self, provider: str):
        if provider == "vertex":
            if self._vertex is None:
                raise KeyError("GOOGLE_CLOUD_PROJECT is not set")
            return self._vertex.client()
        return self._clients[provider]

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
        self.ledger.check()
        kwargs: dict[str, Any] = {
            "model": name,
            "messages": messages,
            **MODEL_PARAMS.get(model, {}),
        }
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

        from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

        empties, discarded = 0, 0.0
        start = time.perf_counter()  # latency covers the whole call, retries and waits included
        for attempt in range(self.max_retries):
            if attempt:
                self.ledger.check()  # the cap is checked again before each retry
            try:
                response = self._client_for(provider).chat.completions.create(**kwargs)
                if response.choices and response.choices[0].message is not None:
                    break
                # Seen on Vertex: a reply with no message. Retry twice, then accept it as an
                # empty answer (the run goes on; the judge sees no answer).
                empties += 1
                error = RuntimeError("the reply had no message")
                if empties >= 3:
                    break
                # A discarded empty reply can still carry billed tokens: charge them now.
                _, lost = _usage_cost(response, provider, model)
                self.ledger.charge(lost, tag or model)
                discarded += lost
            except (RateLimitError, APIConnectionError, APITimeoutError) as exc:
                error = exc
            except APIStatusError as exc:
                if provider == "vertex" and exc.status_code == 401:
                    self._vertex.expire()  # the token expired mid-run: refresh it and retry
                elif exc.status_code < 500:
                    raise
                error = exc
            self.retries += 1
            time.sleep(min(60, 2**attempt) * (0.5 + random.random()))  # jitter spreads retries
        else:
            raise RuntimeError(f"{model}: gave up after {self.max_retries} attempts: {error}")
        latency = time.perf_counter() - start

        empty = not response.choices or response.choices[0].message is None
        choice = None if empty else response.choices[0].message
        usage, cost = _usage_cost(response, provider, model)
        self.ledger.charge(cost, tag or model)
        cost += discarded  # the run's cost includes discarded replies, as the ledger does

        tool_calls = []
        raw_calls = []
        for call in (choice.tool_calls if choice else None) or []:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {"_unparsed": call.function.arguments}
            tool_calls.append({"id": call.id, "name": call.function.name, "arguments": arguments})
            # Kept whole: Gemini 3 puts a thought signature in extra_content that must be sent
            # back with the call on the next turn.
            raw_calls.append(call.model_dump(exclude_none=True))
        text = (choice.content if choice else "") or ""
        message: dict[str, Any] = {"role": "assistant", "content": text}
        if raw_calls:
            message["tool_calls"] = raw_calls
        return Completion(model, text, tool_calls, message, usage, cost, latency)
