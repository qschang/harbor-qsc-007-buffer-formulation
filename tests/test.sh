#!/bin/bash
set -euo pipefail
LOG_DIR=/logs/verifier
REWARD_FILE="$LOG_DIR/reward.txt"
STATUS_FILE="$LOG_DIR/verification-status.txt"
REPORT="$LOG_DIR/pytest-results.xml"
completed=0
mkdir -p "$LOG_DIR"
write_reward(){ chmod 0644 "$REWARD_FILE" 2>/dev/null || true; printf '%s\n' "$1" > "$REWARD_FILE"; chmod 0444 "$REWARD_FILE"; }
on_exit(){ if [ "$completed" -ne 1 ]; then write_reward 0.000; printf '%s\n' 'INCOMPLETE' > "$STATUS_FILE"; fi; }
on_signal(){ write_reward 0.000; completed=1; exit 143; }
write_reward 0.000
trap on_exit EXIT
trap on_signal INT TERM HUP
python3 -m pip install --disable-pip-version-check --no-cache-dir --no-index --find-links=/tests/wheels --require-hashes -r /tests/requirements.txt >/tmp/test-dependencies.log 2>&1
set +e
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONNOUSERSITE=1 timeout --signal=TERM --kill-after=5s 300s python3 -I -m pytest -v -p no:cacheprovider --junitxml="$REPORT" /tests/test_contract.py
rc=$?
set -e
if [ "$rc" -ne 0 ]; then write_reward 0.000; completed=1; exit "$rc"; fi
if [ ! -s "$REPORT" ]; then write_reward 0.000; completed=1; exit 2; fi
if ! python3 -I /tests/score.py --config /tests/scoring.json --junit "$REPORT" --report-out "$LOG_DIR/scoring-report.json" --reward-out "$REWARD_FILE"; then write_reward 0.000; completed=1; exit 2; fi
REWARD=$(cat "$REWARD_FILE")
case "$REWARD" in 0.[0-9][0-9][0-9]|1.000) ;; *) write_reward 0.000; completed=1; exit 2 ;; esac
printf 'COMPLETED: pytest structured report verified; reward=%s\n' "$REWARD" > "$STATUS_FILE"
completed=1

