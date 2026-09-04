#!/usr/bin/env python3
"""扫描需求池 issue，生成应回原群的用户闭环/阶段性闭环通知。

用途：
- product_steward_scan_once.sh 负责负责人区管理同步；
- 本脚本负责原群用户侧通知，避免 Loop/PM/QC 已完成阶段判断但群内无闭环。

输出：
- 无需通知时输出空字符串。
- 有通知时输出可直接发送到主群的文本。

规则：
- status/accepted：阶段性闭环，只通知一次：已采纳、验收标准已确认，等待实现/排期。
- status/done 或 GitHub CLOSED：最终闭环，只通知一次：已完成/关闭。
- status/wontfix：最终闭环，只通知一次：不采纳/关闭，并说明状态。
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Any


def gh_json(*args: str, repo: str) -> Any:
    cmd = [shutil.which("gh") or "/home/mlclaw/.local/bin/gh"]
    if repo:
        cmd += ["--repo", repo]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ERROR: {r.stderr}", file=sys.stderr)
        sys.exit(1)
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


def load_feedbackers(path: str) -> dict[int, list[dict[str, str]]]:
    feedbackers: dict[int, list[dict[str, str]]] = {}
    p = pathlib.Path(path)
    if not p.exists():
        return feedbackers
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
        person = {"name": row.get("feedbacker") or "", "uid": row.get("feedbacker_uid") or ""}
        if person not in feedbackers.setdefault(int(num), []):
            feedbackers[int(num)].append(person)
    return feedbackers


def mention(person: dict[str, str]) -> str:
    uid = person.get("uid") or ""
    name = person.get("name") or ""
    if uid and name:
        return f"@[{uid}:{name}]"
    if name:
        return f"@{name}"
    return "反馈人未知"


def status_label(issue: dict[str, Any]) -> str:
    labels = [l["name"] if isinstance(l, dict) else str(l) for l in issue.get("labels", [])]
    return next((x for x in labels if x.startswith("status/")), "")


def stage_for(issue: dict[str, Any]) -> str:
    st = status_label(issue)
    if issue.get("state") == "CLOSED" or st == "status/done":
        return "done"
    if st == "status/wontfix":
        return "wontfix"
    if st == "status/accepted":
        return "accepted"
    return ""


def format_msg(issue: dict[str, Any], stage: str, people: list[dict[str, str]]) -> str:
    targets = " ".join(mention(p) for p in people) if people else "反馈人未知"
    title = issue.get("title") or ""
    if stage == "accepted":
        return (
            f"{targets} 你反馈的「{title}」已完成产品分诊并被采纳。\n"
            "处理结果：已进入需求池跟踪，PM/QC 已确认验收方向；后续等待实现/排期，有进展我再同步。"
        )
    if stage == "done":
        return (
            f"{targets} 你反馈的「{title}」已完成/关闭。\n"
            "处理结果：需求池已到完成状态。需要追溯详情我可以再补 issue 编号/链接。"
        )
    if stage == "wontfix":
        return (
            f"{targets} 你反馈的「{title}」已关闭为暂不处理。\n"
            "处理结果：产品侧已记录结论；如你需要，我可以补充原因和 issue 编号。"
        )
    return ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Tan6yGu0/octo-cli-product-hub")
    ap.add_argument("--ledger", default="runs/feedback-ledger.jsonl")
    ap.add_argument("--state-file", default="runs/user-closure-state.json")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--init", action="store_true", help="只初始化当前状态，不输出通知")
    args = ap.parse_args()

    feedbackers = load_feedbackers(args.ledger)
    state = load_json(args.state_file, {})
    issues = gh_json(
        "issue", "list", "--state", "all",
        "--limit", str(args.limit),
        "--json", "number,title,state,labels,updatedAt,url",
        repo=args.repo,
    )

    messages: list[str] = []
    for issue in issues:
        num = int(issue["number"])
        if num not in feedbackers:
            continue
        stage = stage_for(issue)
        if not stage:
            continue
        rec = state.setdefault(str(num), {"notified": []})
        notified = set(rec.get("notified") or [])
        if stage not in notified and not args.init:
            msg = format_msg(issue, stage, feedbackers[num])
            if msg:
                messages.append(msg)
        notified.add(stage)
        rec["notified"] = sorted(notified)
        rec["last_status"] = status_label(issue)
        rec["last_state"] = issue.get("state")
        rec["title"] = issue.get("title")
        rec["updatedAt"] = issue.get("updatedAt")

    save_json(args.state_file, state)
    if messages:
        print("\n\n".join(messages))


if __name__ == "__main__":
    main()
