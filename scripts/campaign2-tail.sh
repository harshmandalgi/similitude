#!/usr/bin/env bash
# Re-prioritised tail of campaign2's W2/W3 lane (2026-10-14 22:00): the user's core idea
# (simulated tools) on every workflow before the cheaper-model test; prompt shrinking dropped.
cd "$(dirname "$0")/.."  # run from scripts/: the repo root
RUN="uv run python scripts/run.py"
TAU_CORE="base e-step-procedure e-verify-item-ids m-no-auth m-no-confirm m-8-steps model-gemini-3.8-flash model-gemini-3.1-flash-lite"
log() { echo "[$(date +%H:%M:%S)] $*"; }
while pgrep -f "run.py tau mini B3-cheap-user" > /dev/null; do sleep 30; done
log "W3: planner with simulated tools"; $RUN research mini P-C1-pure --workers 5
log "W2: simulated shop tools (core)";  $RUN tau mini C1-pure --workers 4 --variants $TAU_CORE
log "W3: planner with cheaper model";   $RUN research mini P-B3-cheap --workers 5
log "W2+W3: judge"; $RUN tau judge --judge-workers 2; $RUN research judge --judge-workers 2
log "lane3 done"
