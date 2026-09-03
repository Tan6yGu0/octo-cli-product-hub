#!/usr/bin/env python3
"""扫描需求池 issue 变化，供产品管家做群内通知。

设计原则：
- 无变化输出 []，调用方不要发群消息。
- PM/考官可能只在 GitHub issue 中操作；产品管家通过本脚本发现变化。
- 闭环通知由产品管家发，优先 @ ledger 中记录的原始反馈人。

用法:
  python3 scripts/scan_issues.py [--state-file runs/issue-scan-state.json] [--ledger runs/feedback-ledger.jsonl]
"""
import argparse
import json
import os
import subprocess
import sys

DONE_LABELS = {"status/done", "status/wontfix"}


def gh_json(*args, repo=None):
    cmd = ["gh"]
    if repo:
        cmd += ["--repo", repo]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ERROR: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(r.stdout) if r.stdout.strip() else []


def load_seen(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return {int(k): v for k, v in json.load(f).items()}


def load_feedbackers(path):
    feedbackers = {}
    if not os.path.exists(path):
        return feedbackers
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            num = row.get("issue")
            if not num:
                continue
            entry = feedbackers.setdefault(int(num), [])
            person = {
                "name": row.get("feedbacker") or "",
                "uid": row.get("feedbacker_uid") or "",
            }
            if person not in entry:
                entry.append(person)
    return feedbackers


def status_label(labels):
    return next((l for l in labels if l.startswith("status/")), "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Tan6yGu0/octo-cli-product-hub")
    ap.add_argument("--state-file", default="runs/issue-scan-state.json")
    ap.add_argument("--ledger", default="runs/feedback-ledger.jsonl")
    args = ap.parse_args()

    issues = gh_json(
        "issue", "list", "--state", "all",
        "--json", "number,title,state,labels,updatedAt,url",
        "--limit", "100", repo=args.repo,
    )
    seen = load_seen(args.state_file)
    feedbackers = load_feedbackers(args.ledger)

    changes = []
    for issue in issues:
        num = int(issue["number"])
        labels = sorted(l["name"] if isinstance(l, dict) else l for l in issue.get("labels", []))
        current = {
            "title": issue["title"],
            "state": issue["state"],
            "labels": labels,
            "status": status_label(labels),
            "updatedAt": issue["updatedAt"],
            "url": issue.get("url", ""),
        }
        previous = seen.get(num)
        if previous is None:
            kind = "new"
        elif previous != current:
            kind = "changed"
        else:
            seen[num] = current
            continue

        notify = None
        old_status = previous.get("status") if isinstance(previous, dict) else ""
        new_status = current["status"]
        if issue["state"] == "CLOSED" or (new_status in DONE_LABELS and old_status != new_status):
            notify = {
                "audience": "feedbacker",
                "reason": "closed" if issue["state"] == "CLOSED" else new_status,
                "feedbackers": feedbackers.get(num, []),
                "fallback": "反馈人未知" if not feedbackers.get(num) else "",
            }
        elif new_status and old_status != new_status:
            notify = {"audience": "product-steward", "reason": "status-change"}

        changes.append({"number": num, "type": kind, **current, "previous": previous, "notify": notify})
        seen[num] = current

    os.makedirs(os.path.dirname(args.state_file), exist_ok=True)
    with open(args.state_file, "w") as f:
        json.dump({str(k): v for k, v in seen.items()}, f, indent=2, ensure_ascii=False)

    print(json.dumps(changes, ensure_ascii=False, indent=2) if changes else "[]")


if __name__ == "__main__":
    main()
