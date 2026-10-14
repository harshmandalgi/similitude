#!/usr/bin/env bash
# The whole experiment, in priority order, one lane per workflow (lanes run in parallel).
# Cheap, high-value minis first; expensive simulated-tool minis later, on a core subset of
# variants. The shared ledger stops every lane at the cap (SIMILITUDE_CAP_USD).
#
#   SIMILITUDE_CAP_USD=40 nohup scripts/campaign.sh > runs/logs/campaign.log 2>&1 &
set -u
cd "$(dirname "$0")/.."
RUN="uv run python scripts/run.py"
J="--judge-workers 2"

W1_CORE="base e-question-decomposition e-answer-normalisation e-page-reading-strategy m-3-steps m-2-steps m-no-tools m-one-page model-gemini-3.8-flash model-gemini-3.1-flash-lite"
TAU_CORE="base e-step-procedure e-verify-item-ids m-no-auth m-no-confirm m-8-steps model-gemini-3.8-flash model-gemini-3.1-flash-lite"

log() { echo "[$(date +%H:%M:%S)] $*"; }
wait_for() { while pgrep -f "scripts/run.py $1 full" > /dev/null; do sleep 60; done; }

lane_w1() {
  wait_for wikiqa
  log "W1: ground truth (new mutants)"; $RUN wikiqa full --workers 4
  log "W1: judge";                      $RUN wikiqa judge $J
  log "W1: cheap minis";                $RUN wikiqa mini C2-fused C2+B4 B4-quarter --workers 4
  log "W1: noise ceiling";              $RUN wikiqa mini full-rerun --workers 4 --variants $W1_CORE
  log "W1: short outputs";              $RUN wikiqa mini C6-short-obs --workers 4
  log "W1: judge";                      $RUN wikiqa judge $J
  log "W1: simulated tools";            $RUN wikiqa mini C1-cache-sim C1-pure --workers 4 --variants $W1_CORE
  log "W1: judge";                      $RUN wikiqa judge $J
  log "W1: fix transfer"
  uv run python scripts/fix_transfer.py evidence C2-fused C1-cache-sim
  uv run python scripts/fix_transfer.py write C2-fused C1-cache-sim
  uv run python scripts/fix_transfer.py run C2-fused C1-cache-sim
  log "W1: done"
}

lane_w3() {
  wait_for research
  log "W3: judge";       $RUN research judge $J
  log "W3: cheap minis"; $RUN research mini W-A-replay W-A+B1+C5 W-C4-stub P-C4-stub P-C2-all P-C4+B1+C5 --workers 4
  log "W3: judge";       $RUN research judge $J
  log "W3: cheaper off-focus model, simulated tools"
  $RUN research mini P-B3-cheap P-C1-pure W-B3-cheap --workers 4
  log "W3: judge";       $RUN research judge $J
  log "W3: done"
}

lane_tau() {
  wait_for tau
  log "W2: judge";       $RUN tau judge $J
  log "W2: cheap minis"; $RUN tau mini C2-all B2-cap-turns B3-cheap-user --workers 3
  log "W2: judge";       $RUN tau judge $J
  log "W2: shrunk policy, simulated tools"
  $RUN tau mini C3-shrink-policy C1-pure --workers 3 --variants $TAU_CORE
  log "W2: judge";       $RUN tau judge $J
  log "W2: done"
}

lane_w1 > runs/logs/lane-w1.log 2>&1 &
lane_w3 > runs/logs/lane-w3.log 2>&1 &
lane_tau > runs/logs/lane-tau.log 2>&1 &
wait
log "campaign finished"
