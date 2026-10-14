#!/usr/bin/env bash
# The rest of the experiment in strict priority order (replaces campaign.sh after its first steps).
# Two lanes run in parallel; within each lane, steps run in order of value per dollar, so if the
# shared ledger hits the cap (SIMILITUDE_CAP_USD) only the least important steps are lost.
#
#   SIMILITUDE_CAP_USD=40 nohup scripts/campaign2.sh > runs/logs/campaign2.log 2>&1 &
set -u
cd "$(dirname "$0")/.."
RUN="uv run python scripts/run.py"
J="--judge-workers 2"
W1_CORE="base e-question-decomposition e-answer-normalisation e-page-reading-strategy m-3-steps m-2-steps m-no-tools m-one-page model-gemini-3.8-flash model-gemini-3.1-flash-lite"
TAU_CORE="base e-step-procedure e-verify-item-ids m-no-auth m-no-confirm m-8-steps model-gemini-3.8-flash model-gemini-3.1-flash-lite"

log() { echo "[$(date +%H:%M:%S)] $*"; }
wait_for() { while pgrep -f "scripts/run.py $1" > /dev/null; do sleep 60; done; }

lane_w1() {
  wait_for "wikiqa mini"
  log "W1: judge";                         $RUN wikiqa judge $J
  log "W1: noise ceiling (core)";          $RUN wikiqa mini full-rerun --workers 5 --variants $W1_CORE
  log "W1: judge";                         $RUN wikiqa judge $J
  log "W1: fix transfer (C2-fused)"
  uv run python scripts/fix_transfer.py evidence C2-fused
  uv run python scripts/fix_transfer.py write C2-fused
  uv run python scripts/fix_transfer.py run C2-fused
  log "W1: simulated tools, cache first (core)"; $RUN wikiqa mini C1-cache-sim --workers 5 --variants $W1_CORE
  log "W1: judge";                         $RUN wikiqa judge $J
  log "W1: simulated tools, pure (core)";  $RUN wikiqa mini C1-pure --workers 5 --variants $W1_CORE
  log "W1: judge";                         $RUN wikiqa judge $J
  log "W1: short outputs (core)";          $RUN wikiqa mini C6-short-obs --workers 5 --variants $W1_CORE
  log "W1: judge";                         $RUN wikiqa judge $J
  log "W1: done"
}

lane_w2_w3() {
  wait_for "tau full"
  log "W2: judge";                $RUN tau judge $J
  log "W2: whole conversation as one call"; $RUN tau mini C2-all --workers 4
  log "W2: judge";                $RUN tau judge $J
  wait_for "research full"
  log "W3: judge";                $RUN research judge $J
  log "W3: cheap minis"
  $RUN research mini W-A-replay W-A+B1+C5 P-C2-all P-C4-stub W-C4-stub P-C4+B1+C5 --workers 5
  log "W3: judge";                $RUN research judge $J
  log "W2: cheaper simulated customer (core)"; $RUN tau mini B3-cheap-user --workers 4 --variants $TAU_CORE
  log "W3: planner minis with simulated tools / cheaper model"
  $RUN research mini P-B3-cheap P-C1-pure --workers 5
  log "W2: simulated shop tools (core)"; $RUN tau mini C1-pure --workers 4 --variants $TAU_CORE
  log "W2: shrunk policy (core)"; $RUN tau mini C3-shrink-policy --workers 4 --variants $TAU_CORE
  log "W2+W3: judge";             $RUN tau judge $J; $RUN research judge $J
  log "W2+W3: done"
}

lane_w1 > runs/logs/lane2-w1.log 2>&1 &
lane_w2_w3 > runs/logs/lane2-w23.log 2>&1 &
wait
log "campaign2 finished"
