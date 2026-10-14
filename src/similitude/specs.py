"""Everything the driver needs to know about each workflow: tasks, variants, focus groups, the
recipes built for each group, and the judge."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from similitude.core import Variant, Workflow
from similitude.reduce import GENERIC, RERUN, Recipe
from similitude.workflows import research, tau, wikiqa


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
    truth: Callable | None = None  # a benchmark's own pass/fail, if it has one


W1_RECIPES = [
    RERUN,
    *GENERIC,
    Recipe("C2-fused", "The whole agent loop as one call with imagined tool results.",
           fuse=frozenset({"agent"})),
    Recipe("B4-quarter", "A fixed random quarter of the tasks.", task_fraction=0.25),
    Recipe("C1+C6", "Cached real tools, faked misses, outputs cut to 1,200 characters.",
           llm_replay=True, tool_cache=True, tool_sim="cache_sim", obs_chars=1200),
    Recipe("C2+B4", "Fused loop on a quarter of the tasks.", fuse=frozenset({"agent"}),
           task_fraction=0.25),
]  # fmt: skip

CHEAP = "vertex:google/gemini-3.1-flash-lite"
_W = frozenset({"summary"})
W3_WRITER = [
    RERUN.but("W-rerun", focus="writer"),
    Recipe("W-A-replay", "Replay planner and research from the base's recordings.",
           focus="writer", llm_replay=True, tool_cache=True),
    Recipe("W-B1-slice", "Drop the unscored summary branch.", focus="writer", skip=_W),
    Recipe("W-C5-stop", "Stop after the writer: no review, no revision.", focus="writer",
           stop_after="writer", skip=_W),
    Recipe("W-B3-cheap", "Every node but the writer on gemini-3.1-flash-lite.", focus="writer",
           off_focus_model=CHEAP),
    Recipe("W-C4-stub", "Each researcher is one call that imagines its searches.",
           focus="writer", fuse=frozenset({"researcher"})),
    Recipe("W-A+B1+C5", "Replay upstream, drop the summary, stop after the writer.",
           focus="writer", llm_replay=True, tool_cache=True, skip=_W, stop_after="writer"),
]  # fmt: skip
W3_PLANNER = [
    RERUN.but("P-rerun", focus="planner"),
    Recipe("P-A-replay", "Replay identical calls; tool outputs cached.", focus="planner",
           llm_replay=True, tool_cache=True),
    Recipe("P-C1-cache-sim", "Researchers' tools: recorded if seen, else faked.",
           focus="planner", llm_replay=True, tool_cache=True, tool_sim="cache_sim"),
    Recipe("P-C1-pure", "Researchers' tools all faked from their descriptions.", focus="planner",
           tool_sim="pure"),
    Recipe("P-C4-stub", "Each researcher is one call that imagines its searches.",
           focus="planner", fuse=frozenset({"researcher"})),
    Recipe("P-B3-cheap", "Every node but the planner on gemini-3.1-flash-lite.", focus="planner",
           off_focus_model=CHEAP),
    Recipe("P-C4+B1+C5", "Stubbed researchers, no summary, stop after the writer.",
           focus="planner", fuse=frozenset({"researcher"}), skip=_W, stop_after="writer"),
    Recipe("P-C2-all", "The whole pipeline as ONE call: plan, imagined research, answer.",
           focus="planner", fuse_all=True),
]  # fmt: skip

W2_RECIPES = [
    RERUN,
    Recipe("A-replay", "Replay identical LLM and tool calls from recordings and across variants.",
           llm_replay=True, tool_cache=True),
    Recipe("B3-cheap-user", "The simulated customer on gemini-3.1-flash-lite.", off_focus_model=CHEAP),
    Recipe("B2-cap-turns", "At most 6 agent replies to the customer.", max_steps=6),
    Recipe("B4-half", "A fixed random half of the tasks.", task_fraction=0.5),
    Recipe("C1-pure", "An LLM fakes the shop's tools (database included).", tool_sim="pure"),
    Recipe("C1-cache-sim", "Replay recorded tool outputs; fake only calls never seen.",
           llm_replay=True, tool_cache=True, tool_sim="cache_sim"),
    Recipe("C3-shrink-policy", "The shop policy compressed to about a third.",
           shrink=frozenset({"policy"})),
    Recipe("C2-all", "The whole conversation as ONE call: agent, customer and tools imagined.",
           fuse_all=True),
]  # fmt: skip

SPECS = {
    "wikiqa": Spec(
        wikiqa.WikiQA(), wikiqa.load_tasks, wikiqa.variants,
        lambda vs: {"agent": [v.name for v in vs]}, {"agent": W1_RECIPES},
        wikiqa.JUDGE_SYSTEM, wikiqa.judge_item, wikiqa.rule, wikiqa.CATEGORIES,
    ),
    "wikiqa-openai": Spec(
        wikiqa.WikiQAOpenAI(), wikiqa.load_tasks, wikiqa.openai_variants,
        lambda vs: {"agent": [v.name for v in vs]}, {"agent": W1_RECIPES},
        wikiqa.JUDGE_SYSTEM, wikiqa.judge_item, wikiqa.rule, wikiqa.CATEGORIES,
    ),
    "research": Spec(
        research.Research(), research.load_tasks, research.variants, research.groups,
        {"writer": W3_WRITER, "planner": W3_PLANNER},
        research.JUDGE_SYSTEM, research.judge_item, research.rule, research.CATEGORIES,
    ),
    "tau": Spec(
        tau.TauRetail(), tau.load_tasks, tau.variants, lambda vs: {"agent": [v.name for v in vs]},
        {"agent": W2_RECIPES}, tau.JUDGE_SYSTEM, tau.judge_item, tau.rule, tau.CATEGORIES,
        tau.truth,
    ),
}  # fmt: skip
