"""Recipes: a named list of reduction operators (docs/02-IDEAS.md §3).

A recipe only *configures* the Runtime; the Runtime applies it at each LLM or tool call.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Recipe:
    name: str
    description: str = ""
    focus: str | None = None  # the node under test, when the recipe is built for one focus
    # Group A: free wins
    llm_replay: bool = False  # A1 prefix replay + A3 paired runs: reuse identical LLM calls
    tool_cache: bool = False  # A2: replay recorded real tool outputs for identical calls
    # Group B: small risk
    skip: frozenset[str] = field(default_factory=frozenset)  # B1: nodes the workflow may drop
    max_steps: int | None = None  # B2: cap agent loops
    off_focus_model: str | None = None  # B3: cheaper model for nodes not under test
    task_fraction: float = 1.0  # B4: run on a subset of tasks
    # Group C: must be checked
    tool_sim: str | None = None  # C1: None | "pure" | "grounded" | "cache_sim"
    sim_model: str = "vertex:google/gemini-3.1-flash-lite"  # cheapest output: fake pages are long
    error_injection: bool = False  # C1 guard: fail at the real tool's measured failure rate
    fuse: frozenset[str] = field(default_factory=frozenset)  # C2/C4: agent nodes run as one call
    fuse_all: bool = False  # C2 at workflow level: the whole pipeline as one call
    shrink: frozenset[str] = field(default_factory=frozenset)  # C3: compress these nodes' prompts
    stop_after: str | None = None  # C5: stop after this node and judge its output
    obs_chars: int | None = None  # C6: cut every tool output to this many characters

    @property
    def is_full(self) -> bool:
        return self == Recipe(self.name, self.description)

    def but(self, name: str, **changes) -> Recipe:
        return replace(self, name=name, **changes)


FULL = Recipe("full", "The real workflow, unchanged. Ground truth.")
# The noise ceiling: the full workflow run a second time with fresh samples. No mini can agree
# with the full workflow more than the full workflow agrees with itself.
RERUN = Recipe("full-rerun", "The full workflow again, fresh samples: the noise ceiling.")

# Recipes that apply to any workflow. Workflow-specific ones (slice, early stop, shrink) are
# built next to the workflow.
GENERIC = [
    Recipe("A-replay", "Replay identical LLM and tool calls from recordings and across variants.",
           llm_replay=True, tool_cache=True),
    Recipe("C1-pure", "An LLM fakes every tool from its description only.", tool_sim="pure"),
    Recipe("C1-grounded", "An LLM fakes every tool, shown real recorded outputs of other tasks.",
           tool_sim="grounded"),
    Recipe("C1-cache-sim", "Replay recorded tool outputs; fake only calls never seen.",
           llm_replay=True, tool_cache=True, tool_sim="cache_sim"),
    Recipe("C1-cache-sim-err", "As C1-cache-sim, plus failures at the real tool's rate.",
           llm_replay=True, tool_cache=True, tool_sim="cache_sim", error_injection=True),
    Recipe("C6-short-obs", "Tool outputs cut to 1,200 characters.", obs_chars=1200),
    Recipe("B2-cap-steps", "Agent loops capped at 4 steps.", max_steps=4),
]  # fmt: skip
