"""Ask a fresh, blind Claude Code instance for a JSON answer (judging, labelling, writing variants).

One `claude -p` call per question, with the local Claude Code login (API-key variables are
removed from its environment), no tools, no CLAUDE.md, memory, skills or MCP servers
(`--safe-mode`), no saved session, in an empty folder, and with our instructions as the whole
system prompt. Every answer is kept under runs/claude/ so it can be audited.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BILLING_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL")
OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"


def json_in(text: str) -> Any:
    """The JSON object in an answer (it may sit in a code fence)."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in the answer")
    return json.loads(text[start : end + 1])


def ask_claude(
    system: str,
    user: str,
    *,
    model: str = OPUS,
    effort: str = "high",
    keep_dir: Path | None = None,
    name: str = "",
    attempts: int = 3,
    timeout_s: int = 1800,
) -> Any:
    env = {k: v for k, v in os.environ.items() if k not in BILLING_VARS}
    command = [
        "claude", "-p",
        "--model", model,
        "--effort", effort,
        "--tools", "",
        "--safe-mode",
        "--no-session-persistence",
        "--output-format", "json",
        "--system-prompt", system,
    ]  # fmt: skip
    error = ""
    for _ in range(attempts):
        with tempfile.TemporaryDirectory(prefix="blank-") as empty:
            try:
                done = subprocess.run(
                    command, input=user, capture_output=True, text=True, cwd=empty, env=env, check=False,
                    timeout=timeout_s,
                )  # fmt: skip
            except subprocess.TimeoutExpired:
                error = "timed out"
                continue
        try:
            envelope = json.loads(done.stdout)
        except json.JSONDecodeError:
            error = f"not JSON: {done.stdout[:200]} {done.stderr[:200]}"
            continue
        if envelope.get("is_error"):
            error = str(envelope.get("result"))[:300]
            continue
        text = str(envelope.get("result") or "")
        used = sorted((envelope.get("modelUsage") or {}).keys())
        if model not in used:
            error = f"answered by {used}, not {model}"
            continue
        try:
            answer = json_in(text)
        except ValueError as exc:
            error = str(exc)
            continue
        if keep_dir is not None:
            keep_dir.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256((system + user).encode()).hexdigest()[:12]
            record = {
                "model": model,
                "effort": effort,
                "usage": (envelope.get("modelUsage") or {}).get(model),
                "duration_ms": envelope.get("duration_ms"),
                "answered_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "system": system,
                "user": user,
                "text": text,
            }
            path = keep_dir / f"{name or 'call'}-{digest}.json"
            path.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n")
        return answer
    raise RuntimeError(f"Claude Code gave no usable answer after {attempts} attempts: {error}")
