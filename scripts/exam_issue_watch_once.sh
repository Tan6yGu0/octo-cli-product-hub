#!/usr/bin/env bash
set -euo pipefail

export PATH="/home/mlclaw/.npm-global/bin:/home/mlclaw/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

cd /home/mlclaw/.openclaw/workspace/octo-cli-product-hub

OWNER='@[0cb0e235d14443d88f8803f54e19faf4:郭尘泽]'
OWNER_THREAD_ID='506434bca8944409a2c9671d530ed460____2095458049580863488'
LOG_DIR="runs"
ERROR_STATE="$LOG_DIR/exam-issue-watcher-error-state.json"
ERROR_THROTTLE_SEC=900
mkdir -p "$LOG_DIR"

notify_error() {
  local kind="$1"
  local text="$2"
  python3 - "$ERROR_STATE" "$kind" "$ERROR_THROTTLE_SEC" <<'PY' || return 0
import json, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
kind = sys.argv[2]
throttle = int(sys.argv[3])
now = int(time.time())
try:
    data = json.loads(path.read_text()) if path.exists() else {}
except Exception:
    data = {}
last = int(data.get(kind, 0) or 0)
if now - last < throttle:
    raise SystemExit(1)
data[kind] = now
path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
PY
  octo-cli --profile changming message send \
    --channel-id "$OWNER_THREAD_ID" \
    --channel-type 5 \
    --data "$(python3 -c 'import json,sys; print(json.dumps({"payload":{"type":1,"content":sys.argv[1]}} , ensure_ascii=False))' "$text")" \
    >/dev/null || true
}

if ! git pull --ff-only --autostash >>"$LOG_DIR/exam-issue-watcher.log" 2>>"$LOG_DIR/exam-issue-watcher.err.log"; then
  err=$(tail -c 500 "$LOG_DIR/exam-issue-watcher.err.log" | tr '\n' ' ')
  notify_error "git_pull" "$OWNER [产品管家] 需求池外部操作扫描异常：git pull 失败，已停止本轮扫描。${err:+ 错误：$err}"
  exit 0
fi

if ! python3 scripts/exam_issue_watcher.py --send --loop >>"$LOG_DIR/exam-issue-watcher.log" 2>>"$LOG_DIR/exam-issue-watcher.err.log"; then
  err=$(tail -c 500 "$LOG_DIR/exam-issue-watcher.err.log" | tr '\n' ' ')
  notify_error "watcher" "$OWNER [产品管家] 需求池外部操作扫描异常/可能限流：已停止本轮扫描，不做高频重试。${err:+ 错误：$err}"
fi
