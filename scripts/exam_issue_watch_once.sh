#!/usr/bin/env bash
set -euo pipefail

export PATH="/home/mlclaw/.npm-global/bin:/home/mlclaw/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

cd /home/mlclaw/.openclaw/workspace/octo-cli-product-hub

CHANNEL_CONFIG="${FDE_CHANNEL_CONFIG:-config/fde_channels.json}"
OWNER="$(python3 - <<'PY'
import json, pathlib
p=pathlib.Path('config/fde_channels.json')
if p.exists():
    c=json.loads(p.read_text())
    o=c.get('owner', {})
    uid=o.get('uid','0cb0e235d14443d88f8803f54e19faf4')
    name=o.get('name','郭尘泽')
else:
    uid='0cb0e235d14443d88f8803f54e19faf4'; name='郭尘泽'
print(f'@[{uid}:{name}]')
PY
)"
OWNER_THREAD_ID="$(python3 - <<'PY'
import json, pathlib
p=pathlib.Path('config/fde_channels.json')
if p.exists():
    print((json.loads(p.read_text()).get('owner_thread') or {}).get('channel_id','506434bca8944409a2c9671d530ed460____2095458049580863488'))
else:
    print('506434bca8944409a2c9671d530ed460____2095458049580863488')
PY
)"
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

# Best-effort code update only. GitHub network hiccups must not become
# user-visible "scan failed" noise, and issue scanning does not depend on git pull.
if ! git pull --ff-only --autostash >>"$LOG_DIR/exam-issue-watcher.log" 2>>"$LOG_DIR/exam-issue-watcher.err.log"; then
  echo "$(date -Is) WARN git pull failed; continue with current checkout" >>"$LOG_DIR/exam-issue-watcher.log"
fi

if ! python3 scripts/exam_issue_watcher.py --config "$CHANNEL_CONFIG" --send --loop >>"$LOG_DIR/exam-issue-watcher.log" 2>>"$LOG_DIR/exam-issue-watcher.err.log"; then
  err=$(tail -c 500 "$LOG_DIR/exam-issue-watcher.err.log" | tr '\n' ' ')
  notify_error "watcher" "$OWNER [产品管家] 需求池外部操作扫描异常/可能限流：已停止本轮扫描，不做高频重试。${err:+ 错误：$err}"
fi
