"""Stand-ins for tau_bench.types (which uses pydantic), enough for tasks_test.py."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Action:
    name: str
    kwargs: dict[str, Any]


@dataclass
class Task:
    user_id: str
    actions: list[Action]
    instruction: str
    outputs: list[str] = field(default_factory=list)
    annotator: str = ""
