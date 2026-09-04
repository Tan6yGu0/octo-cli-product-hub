#!/usr/bin/env python3
"""Watch GitHub demand-pool issues for silent examiner/owner operations.

Why this exists:
- In the FDE exam, the examiner may operate directly in GitHub (close an issue,
  mark wontfix/done/accepted, add type/feature, etc.) without notifying Octo.
- The product steward must discover those changes via scheduled scanning,
  synchronize Loop state, notify the owner feedback thread, and when appropriate
  close the loop with the original feedbacker in the main group.

Default behavior is conservative:
- First run or --init snapshots current GitHub state and sends nothing.
- Subsequent runs compare state, emit owner/user messages, and optionally update
  Loop tasks when ledger contains loop_task_id.
- Runtime state lives under runs/ and must not be committed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import fcntl
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Any

DEFAULT_REPO = "Tan6yGu0/octo-cli-product-hub"
DEFAULT_LEDGER = "runs/feedback-ledger.jsonl"
DEFAULT_STATE = "runs/exam-issue-watch-state.json"
DEFAULT_CHANNEL_CONFIG = "config/fde_channels.json"
DEFAULT_LOOP_WORKSPACE_ID = "bb4a2752-e52a-4f89-b768-ef1941ee68d2"
DEFAULT_OWNER_CHANNEL_ID = "506434bca8944409a2c9671d530ed460____2095458049580863488"
DEFAULT_OWNER_CHANNEL_TYPE = 5
DEFAULT_MAIN_CHANNEL_ID = "506434bca8944409a2c9671d530ed460"
DEFAULT_MAIN_CHANNEL_TYPE = 2
OWNER = {"uid": "0cb0e235d14443d88f8803f54e19faf4", "name": "郭尘泽"}

STATUS_LABELS = {
    "status/new",
    "status/triaged",
    "status/accepted",
    "status/in-progress",
    "status/done",
    "status/wontfix",
}
FINAL_STAGES = {"done", "wontfix"}


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\nSTDERR: {r.stderr.strip()}\nSTDOUT: {r.stdout.strip()}")
    return r


def gh_json(*args: str, repo: str) -> Any:
    cmd = [shutil.which("gh") or "/home/mlclaw/.local/bin/gh"]
    if repo:
        cmd += ["--repo", repo]
    cmd += list(args)
    r = run(cmd)
    return json.loads(r.stdout) if r.stdout.strip() else []


def load_json(path: str, default: Any) -> Any:
    p = pathlib.Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: str, data: Any) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_channel_config(path: str) -> dict[str, Any]:
    p = pathlib.Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"invalid channel config {path}: {e}")


def cfg_get(cfg: dict[str, Any], section: str, key: str, default: Any) -> Any:
    value = (cfg.get(section) or {}).get(key)
    return default if value in (None, "") else value


def label_names(issue: dict[str, Any]) -> list[str]:
    return sorted(l.get("name", "") if isinstance(l, dict) else str(l) for l in issue.get("labels", []))


def status_label(labels: list[str]) -> str:
    return next((x for x in labels if x.startswith("status/")), "")


def stage_for(state: str, status: str) -> str:
    if status == "status/wontfix":
        return "wontfix"
    if state == "CLOSED" or status == "status/done":
        return "done"
    if status == "status/accepted":
        return "accepted"
    if status == "status/in-progress":
        return "in_progress"
    if status == "status/triaged":
        return "triaged"
    return ""


def issue_snapshot(issue: dict[str, Any]) -> dict[str, Any]:
    labels = label_names(issue)
    return {
        "number": int(issue["number"]),
        "title": issue.get("title") or "",
        "state": issue.get("state") or "",
        "labels": labels,
        "status": status_label(labels),
        "updatedAt": issue.get("updatedAt") or "",
        "url": issue.get("url") or "",
    }


def load_ledger(path: str) -> dict[int, dict[str, Any]]:
    """Return latest known feedback/Loop mapping by GitHub issue number."""
    out: dict[int, dict[str, Any]] = {}
    p = pathlib.Path(path)
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        num = row.get("issue")
        if not num:
            continue
        rec = out.setdefault(int(num), {"feedbackers": []})
        rec.update({k: v for k, v in row.items() if v not in (None, "")})
        person = {"name": row.get("feedbacker") or "", "uid": row.get("feedbacker_uid") or ""}
        if person not in rec["feedbackers"]:
            rec["feedbackers"].append(person)
    return out


def mention(person: dict[str, str]) -> str:
    """Management-thread mention syntax.

    This is only for owner/management messages. User-facing messages sent via
    octo-cli raw payload should not use the bracket mention form because it may
    render as the literal internal id in some clients.
    """
    uid = person.get("uid") or ""
    name = person.get("name") or ""
    if uid and name:
        return f"@[{uid}:{name}]"
    if name:
        return f"@{name}"
    return "反馈人未知"


def display_name(person: dict[str, str]) -> str:
    name = person.get("name") or "反馈人"
    return name if name.startswith("@") else f"@{name}"


def diff_event(previous: dict[str, Any] | None, current: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any] | None:
    if previous is None:
        return None
    if previous == current:
        return None

    old_labels = set(previous.get("labels") or [])
    new_labels = set(current.get("labels") or [])
    added = sorted(new_labels - old_labels)
    removed = sorted(old_labels - new_labels)
    old_status = previous.get("status") or ""
    new_status = current.get("status") or ""
    old_state = previous.get("state") or ""
    new_state = current.get("state") or ""
    stage = stage_for(new_state, new_status)

    reasons: list[str] = []
    if old_state != new_state:
        reasons.append(f"state:{old_state or '-'}→{new_state or '-'}")
    if old_status != new_status:
        reasons.append(f"status:{old_status or '-'}→{new_status or '-'}")
    watched_added = [x for x in added if x.startswith("type/") or x.startswith("priority/") or x.startswith("area/") or x in STATUS_LABELS]
    if watched_added:
        reasons.append("labels:+" + ",".join(watched_added))
    watched_removed = [x for x in removed if x.startswith("type/") or x.startswith("priority/") or x.startswith("area/") or x in STATUS_LABELS]
    if watched_removed:
        reasons.append("labels:-" + ",".join(watched_removed))
    if not reasons:
        # Ignore pure timestamp churn/comment-only changes for now. They can be noisy and
        # usually do not require product-steward action unless labels/state also changed.
        return None

    return {
        "number": current["number"],
        "title": current["title"],
        "url": current["url"],
        "previous": previous,
        "current": current,
        "added_labels": added,
        "removed_labels": removed,
        "stage": stage,
        "reasons": reasons,
        "ledger": ledger,
    }


def owner_message(ev: dict[str, Any]) -> str:
    cur = ev["current"]
    prev = ev["previous"]
    ledger = ev.get("ledger") or {}
    feedbackers = ledger.get("feedbackers") or []
    people = " ".join(mention(p) for p in feedbackers) if feedbackers else "未识别到原始反馈人"
    loop = ledger.get("loop_task_key") or ledger.get("loop_task_id") or "未找到 Loop 映射"
    stage = ev.get("stage") or "普通状态变化"
    next_action = {
        "accepted": "阶段性闭环：负责人已知；最长 Bot 回原群同步“已采纳/等待实现”；Loop 进入 blocked(waiting_on=upstream_implementation)，不是最终完成。",
        "done": "最终闭环：同步负责人，并由最长 Bot 回原群通知已完成/关闭。",
        "wontfix": "最终闭环：同步负责人，并由最长 Bot 回原群通知暂不处理。",
        "in_progress": "处理进展：同步负责人，继续等待实现/后续状态。",
        "triaged": "分诊进展：同步负责人，等待 PM/QC 或实现侧继续推进。",
    }.get(stage, "管理同步：记录考官/PM 在需求池中的静默操作，必要时产品管家继续跟进。")
    return (
        f"{mention(OWNER)} [产品管家] 需求池外部操作已检测。\n"
        f"Issue：#{cur['number']}《{cur['title']}》\n"
        f"变化：{'; '.join(ev['reasons'])}\n"
        f"状态：{prev.get('state')}/{prev.get('status') or '-'} → {cur.get('state')}/{cur.get('status') or '-'}\n"
        f"Loop：{loop}\n"
        f"原始反馈人：{people}\n"
        f"下一步：{next_action}\n"
        f"追溯：{cur['url']}"
    )


def user_message(ev: dict[str, Any]) -> str:
    cur = ev["current"]
    people = (ev.get("ledger") or {}).get("feedbackers") or []
    targets = "、".join(display_name(p) for p in people) if people else "@反馈人"
    title = cur.get("title") or "这条反馈"
    if ev.get("stage") == "accepted":
        return (
            "📋 进展通知\n"
            "以下反馈已采纳，后续等待实现/排期：\n"
            f"{targets} 「{title}」"
        )
    if ev.get("stage") == "done":
        return (
            "📋 闭环通知\n"
            "以下反馈已修复/关闭，感谢大家 🎉\n"
            f"{targets} 「{title}」"
        )
    if ev.get("stage") == "wontfix":
        return (
            "📋 闭环通知\n"
            "以下反馈本次暂不处理，已记录结论：\n"
            f"{targets} 「{title}」"
        )
    return ""


def send_octo(channel_id: str, channel_type: int, content: str) -> None:
    body = {"payload": {"type": 1, "content": content}}
    run([
        "octo-cli", "--profile", "changming", "message", "send",
        "--channel-id", channel_id,
        "--channel-type", str(channel_type),
        "--data", json.dumps(body, ensure_ascii=False),
    ])


def loop_update(ev: dict[str, Any], *, workspace_id: str) -> list[str]:
    ledger = ev.get("ledger") or {}
    loop_id = ledger.get("loop_task_id")
    if not loop_id:
        return ["skip: no loop_task_id in ledger"]

    cur = ev["current"]
    stage = ev.get("stage") or ""
    actions: list[str] = []

    metadata = {
        "github_last_seen_state": cur.get("state") or "",
        "github_last_seen_status": cur.get("status") or "",
        "github_last_seen_labels": ",".join(cur.get("labels") or []),
        "github_last_seen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if stage:
        metadata["pipeline_status"] = stage
    if stage == "accepted":
        metadata["waiting_on"] = "upstream_implementation"
        metadata["closure_semantics"] = "accepted_is_stage_closure_not_final_done"
    if stage == "wontfix":
        metadata["decision"] = "wontfix"
        metadata["waiting_on"] = "none_final_closed"
    elif stage == "done":
        metadata["decision"] = "done"
        metadata["waiting_on"] = "none_final_closed"

    for k, v in metadata.items():
        r = run([
            "octo-daemon", "--workspace-id", workspace_id,
            "issue", "metadata", "set", loop_id,
            "--key", k, "--value", str(v), "--type", "string",
        ], check=False)
        actions.append(f"metadata:{k}:{'ok' if r.returncode == 0 else 'failed'}")

    desired_status = ""
    if stage == "done":
        desired_status = "done"
    elif stage == "wontfix":
        desired_status = "cancelled"
    elif stage == "accepted":
        # Accepted means product triage is complete, but implementation is external
        # to this read-only feedback workspace. Keep the Loop parent open as a
        # waiting state, not done. Final closure is only done/closed/wontfix.
        desired_status = "blocked"
    if desired_status:
        r = run([
            "octo-daemon", "--workspace-id", workspace_id,
            "issue", "status", loop_id, desired_status,
        ], check=False)
        actions.append(f"status:{desired_status}:{'ok' if r.returncode == 0 else 'failed'}")

    comment = (
        "GitHub 需求池外部操作同步：\n\n"
        f"- Issue: #{cur['number']} {cur['url']}\n"
        f"- Title: {cur['title']}\n"
        f"- Change: {'; '.join(ev['reasons'])}\n"
        f"- Current: {cur.get('state')}/{cur.get('status') or '-'}\n"
        f"- Stage: {stage or 'generic'}\n"
        "- Closure semantics: accepted=阶段性闭环/等待上游实现；done/closed/wontfix=最终闭环。\n"
        "\n该记录由 exam_issue_watcher.py 定时扫描生成。"
    )
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as f:
        f.write(comment)
        tmp = f.name
    try:
        r = run([
            "octo-daemon", "--workspace-id", workspace_id,
            "issue", "comment", "add", loop_id, "--content-file", tmp,
        ], check=False)
        actions.append(f"comment:{'ok' if r.returncode == 0 else 'failed'}")
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
    return actions


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=DEFAULT_CHANNEL_CONFIG, help="FDE channel/workspace config JSON")
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--state-file", default=DEFAULT_STATE)
    ap.add_argument("--loop-workspace-id")
    ap.add_argument("--owner-channel-id")
    ap.add_argument("--owner-channel-type", type=int)
    ap.add_argument("--main-channel-id")
    ap.add_argument("--main-channel-type", type=int)
    ap.add_argument("--owner-name")
    ap.add_argument("--owner-uid")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--init", action="store_true", help="snapshot current state and send/update nothing")
    ap.add_argument("--send", action="store_true", help="send owner/user messages through octo-cli")
    ap.add_argument("--loop", action="store_true", help="synchronize Loop task metadata/status/comment when possible")
    ap.add_argument("--dry-run", action="store_true", help="print planned actions only")
    args = ap.parse_args()

    cfg = load_channel_config(args.config)
    args.loop_workspace_id = args.loop_workspace_id or cfg_get(cfg, "loop", "workspace_id", DEFAULT_LOOP_WORKSPACE_ID)
    args.owner_channel_id = args.owner_channel_id or cfg_get(cfg, "owner_thread", "channel_id", DEFAULT_OWNER_CHANNEL_ID)
    args.owner_channel_type = args.owner_channel_type or int(cfg_get(cfg, "owner_thread", "channel_type", DEFAULT_OWNER_CHANNEL_TYPE))
    args.main_channel_id = args.main_channel_id or cfg_get(cfg, "main_group", "channel_id", DEFAULT_MAIN_CHANNEL_ID)
    args.main_channel_type = args.main_channel_type or int(cfg_get(cfg, "main_group", "channel_type", DEFAULT_MAIN_CHANNEL_TYPE))
    owner_name = args.owner_name or cfg_get(cfg, "owner", "name", OWNER["name"])
    owner_uid = args.owner_uid or cfg_get(cfg, "owner", "uid", OWNER["uid"])
    OWNER.update({"name": owner_name, "uid": owner_uid})

    # Prevent cron/manual overlap from emitting duplicate owner/user notices or
    # duplicate Loop comments for the same GitHub transition.
    lock_path = args.state_file + ".lock"
    pathlib.Path(lock_path).parent.mkdir(parents=True, exist_ok=True)
    lock_fh = open(lock_path, "w")
    fcntl.flock(lock_fh, fcntl.LOCK_EX)

    issues = gh_json(
        "issue", "list", "--state", "all",
        "--json", "number,title,state,labels,updatedAt,url",
        "--limit", str(args.limit), repo=args.repo,
    )
    current = {str(s["number"]): s for s in (issue_snapshot(x) for x in issues)}
    previous_state = load_json(args.state_file, {})

    if args.init or not previous_state:
        save_json(args.state_file, current)
        print(json.dumps({"ok": True, "init": True, "count": len(current)}, ensure_ascii=False, indent=2))
        return

    ledger = load_ledger(args.ledger)
    events: list[dict[str, Any]] = []
    for key, cur in current.items():
        ev = diff_event(previous_state.get(key), cur, ledger.get(int(key), {}))
        if ev:
            events.append(ev)

    actions: list[dict[str, Any]] = []
    notified = load_json(args.state_file + ".notified", {})
    user_notified = load_json(args.state_file + ".user_notified", {})
    for ev in events:
        key = str(ev["number"])
        stage = ev.get("stage") or "generic"
        notify_key = f"{ev['current'].get('updatedAt')}|{stage}|{'/'.join(ev['reasons'])}"
        legacy_notices = set(notified.get(key, []))
        already = notify_key in legacy_notices
        owner = owner_message(ev)
        user = user_message(ev) if stage in {"accepted", "done", "wontfix"} else ""

        # Owner/management notices are per GitHub transition. User-facing closure
        # notices are per issue+stage. This prevents repeated "done" messages when
        # a closed issue receives later label/comment churn. Legacy transition
        # records are treated as already sent so adding this guard does not resend
        # old closures after deployment.
        sent_user_stages = set(user_notified.get(key, []))
        legacy_user_already = any(f"|{stage}|" in item for item in legacy_notices)
        user_already = stage in sent_user_stages or legacy_user_already

        loop_actions: list[str] = []
        if not already and args.loop and not args.dry_run:
            loop_actions = loop_update(ev, workspace_id=args.loop_workspace_id)
        if not already and args.send and not args.dry_run:
            send_octo(args.owner_channel_id, args.owner_channel_type, owner)
        user_sent = False
        if (
            user
            and (ev.get("ledger") or {}).get("feedbackers")
            and not user_already
            and args.send
            and not args.dry_run
        ):
            send_octo(args.main_channel_id, args.main_channel_type, user)
            sent_user_stages.add(stage)
            user_notified[key] = sorted(sent_user_stages)
            user_sent = True
        if not already:
            notified.setdefault(key, []).append(notify_key)
        actions.append({
            "issue": ev["number"],
            "stage": stage,
            "reasons": ev["reasons"],
            "owner_message": owner,
            "user_message": user,
            "user_already_notified": user_already,
            "user_sent": user_sent,
            "loop_actions": loop_actions,
            "already_notified": already,
        })

    save_json(args.state_file, current)
    save_json(args.state_file + ".notified", notified)
    save_json(args.state_file + ".user_notified", user_notified)
    print(json.dumps({"ok": True, "events": actions}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
