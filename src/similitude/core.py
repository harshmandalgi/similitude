"""Shared types: tools, variants, workflows, and the trace a run leaves behind."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from similitude.runtime import Runtime


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema of the arguments
    fn: Callable[[dict[str, Any]], str]
    is_failure: Callable[[str], bool] = lambda output: False  # "no results", "not found", ...
    stateful: bool = False  # output depends on earlier calls (a database): never memoised

    def spec(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass(frozen=True)
class Variant:
    """One version of the workflow: the base, an edit, a deliberately broken mutant, a model
    swap, or a fix. `config` overrides the workflow's base config."""

    name: str
    kind: str  # base | edit | mutant | model | fix
    focus: str  # the node this variant changes
    description: str
    config: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)


class Workflow(ABC):
    name: str
    nodes: tuple[str, ...]

    @abstractmethod
    def tools(self) -> dict[str, Tool]: ...

    @abstractmethod
    def base_config(self) -> dict[str, Any]: ...

    @abstractmethod
    def run(self, task: dict[str, Any], rt: Runtime, config: dict[str, Any]) -> str: ...

    def config_for(self, variant: Variant) -> dict[str, Any]:
        """The base config with the variant's overrides merged in, one level deep."""
        config = json.loads(json.dumps(self.base_config()))
        for key, value in variant.config.items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value
        return config


# Where an event's output came from. Only "real" and "sim" calls cost money now;
# "memo" stands for a real call made earlier and counts its recorded latency.
SOURCES = ("real", "memo", "record", "pool", "sim", "imagined")


@dataclass
class Event:
    kind: str  # llm | tool
    node: str
    name: str  # model id or tool name
    source: str
    key: str
    output: str
    args: Any = None
    cost_usd: float = 0.0
    latency_s: float = 0.0
    usage: dict[str, int] | None = None
    completion: dict[str, Any] | None = None  # llm events: what a replay needs


@dataclass
class Trace:
    workflow: str
    recipe: str
    variant: str
    task_id: str
    replicate: int
    final: str = ""
    error: str = ""
    events: list[Event] = field(default_factory=list)

    @property
    def run_id(self) -> str:
        return f"{self.workflow}/{self.recipe}/{self.variant}/{self.task_id}/r{self.replicate}"

    @property
    def cost_usd(self) -> float:
        return sum(e.cost_usd for e in self.events if e.source in ("real", "sim"))

    @property
    def latency_s(self) -> float:
        return sum(e.latency_s for e in self.events if e.source in ("real", "memo", "sim"))

    def count(self, kind: str, sources: tuple[str, ...] = ("real", "memo", "sim")) -> int:
        return sum(1 for e in self.events if e.kind == kind and e.source in sources)

    def to_json(self) -> dict[str, Any]:
        return {
            **{k: v for k, v in asdict(self).items() if k != "events"},
            "run_id": self.run_id,
            "cost_usd": self.cost_usd,
            "latency_s": self.latency_s,
            "events": [asdict(e) for e in self.events],
        }

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> Trace:
        trace = cls(
            d["workflow"], d["recipe"], d["variant"], d["task_id"], d["replicate"],
            d.get("final", ""), d.get("error", ""),
        )  # fmt: skip
        trace.events = [Event(**e) for e in d["events"]]
        return trace

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json(), ensure_ascii=False))

    @classmethod
    def load(cls, path: Path) -> Trace:
        return cls.from_json(json.loads(path.read_text()))

    def trajectory(self, obs_chars: int = 300) -> str:
        """A short, readable account of what the run did, for judges."""
        lines = []
        for e in self.events:
            if e.kind == "tool":
                args = json.dumps(e.args, ensure_ascii=False)
                out = " ".join(e.output.split())[:obs_chars]
                lines.append(f"[{e.node}] {e.name}({args}) -> {out}")
            elif e.output.strip():
                lines.append(f"[{e.node}] says: {' '.join(e.output.split())[:obs_chars]}")
        return "\n".join(lines)
