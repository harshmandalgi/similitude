#!/usr/bin/env bash
# Final steps after the user raised the cap to $75 (2026-10-15): finish tau's simulated-tools
# miniature, retry W3's errored replay runs, then judge everything left. W3's cheaper-model test
# (P-B3-cheap) and tau's prompt shrinking stay dropped.
cd "$(dirname "$0")/.."
RUN="uv run python scripts/run.py"
TAU_CORE="base e-step-procedure e-verify-item-ids m-no-auth m-no-confirm m-8-steps model-gemini-3.8-flash model-gemini-3.1-flash-lite"
log() { echo "[$(date +%H:%M:%S)] $*"; }
log "W2: simulated shop tools (core)"; $RUN tau mini C1-pure --workers 4 --variants $TAU_CORE
log "W3: retry errored replay runs";   $RUN research mini W-A-replay-2 --workers 4
log "judge"; $RUN tau judge --judge-workers 3; $RUN research judge --judge-workers 3; $RUN wikiqa judge --judge-workers 3
log "final done"
