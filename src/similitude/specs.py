"""Everything the driver needs to know about each workflow: tasks, variants, focus groups, the
recipes built for each group, and the judge."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from similitude.core import Variant, Workflow
from similitude.reduce import GENERIC, Recipe
from similitude.workflows import research, wikiqa


@dataclass
class Spec:
    workflow: Workflow
    load_tasks: Callable[[str], list[dict[str, Any]]]
    variants: Callable[[], list[Variant]]
    groups: Callable[[list[Variant]], dict[str, list[str]]]  # group -> variant names
    recipes: dict[str, list[Recipe]]  # group -> the minis built for it
    judge_system: str
    judge_item: Callable
    rule: Callable
    categories: list[str]


W1_RECIPES = [
    *GENERIC,
    Recipe("C2-fused", "The whole agent loop as one call with imagined tool results.",
           fuse=frozenset({"agent"})),
    Recipe("B4-quarter", "A fixed random quarter of the tasks.", task_fraction=0.25),
    Recipe("C1+C6", "Cached real tools, faked misses, outputs cut to 1,200 characters.",
           llm_replay=True, tool_cache=True, tool_sim="cache_sim", obs_chars=1200),
    Recipe("C2+B4", "Fused loop on a quarter of the tasks.", fuse=frozenset({"agent"}),
           task_fraction=0.25),
]  # fmt: skip

CHEAP = "openai:gpt-4.1-nano"
_W = frozenset({"summary"})
W3_WRITER = [
    Recipe("W-A-replay", "Replay planner and research from the base's recordings.",
           focus="writer", llm_replay=True, tool_cache=True),
    Recipe("W-B1-slice", "Drop the unscored summary branch.", focus="writer", skip=_W),
    Recipe("W-C5-stop", "Stop after the writer: no review, no revision.", focus="writer",
           stop_after="writer", skip=_W),
    Recipe("W-B3-cheap", "Every node but the writer on gpt-4.1-nano.", focus="writer",
           off_focus_model=CHEAP),
    Recipe("W-C4-stub", "Each researcher is one call that imagines its searches.",
           focus="writer", fuse=frozenset({"researcher"})),
    Recipe("W-A+B1+C5", "Replay upstream, drop the summary, stop after the writer.",
           focus="writer", llm_replay=True, tool_cache=True, skip=_W, stop_after="writer"),
]  # fmt: skip
W3_PLANNER = [
    Recipe("P-A-replay", "Replay identical calls; tool outputs cached.", focus="planner",
           llm_replay=True, tool_cache=True),
    Recipe("P-C1-cache-sim", "Researchers' tools: recorded if seen, else faked.",
           focus="planner", llm_replay=True, tool_cache=True, tool_sim="cache_sim"),
    Recipe("P-C1-pure", "Researchers' tools all faked from their descriptions.", focus="planner",
           tool_sim="pure"),
    Recipe("P-C4-stub", "Each researcher is one call that imagines its searches.",
           focus="planner", fuse=frozenset({"researcher"})),
    Recipe("P-B3-cheap", "Every node but the planner on gpt-4.1-nano.", focus="planner",
           off_focus_model=CHEAP),
    Recipe("P-C4+B1+C5", "Stubbed researchers, no summary, stop after the writer.",
           focus="planner", fuse=frozenset({"researcher"}), skip=_W, stop_after="writer"),
    Recipe("P-C2-all", "The whole pipeline as ONE call: plan, imagined research, answer.",
           focus="planner", fuse_all=True),
]  # fmt: skip

SPECS = {
    "wikiqa": Spec(
        wikiqa.WikiQA(), wikiqa.load_tasks, wikiqa.variants,
        lambda vs: {"agent": [v.name for v in vs]}, {"agent": W1_RECIPES},
        wikiqa.JUDGE_SYSTEM, wikiqa.judge_item, wikiqa.rule, wikiqa.CATEGORIES,
    ),
    "research": Spec(
        research.Research(), research.load_tasks, research.variants, research.groups,
        {"writer": W3_WRITER, "planner": W3_PLANNER},
        research.JUDGE_SYSTEM, research.judge_item, research.rule, research.CATEGORIES,
    ),
}  # fmt: skip
