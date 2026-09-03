#!/usr/bin/env python3
"""Format issue/PRD changes for the product steward's group notification.

This script only prints the message body; the product steward decides whether to send it.
Rules:
- Empty changes => print nothing and exit 0 (no group message).
- Business notifications mention original feedbackers when available.
- PM is not a group-facing bot by default; PM writes issue comments, then the product steward scans and notifies.
"""
import argparse
import json
import sys


def mention(person):
    uid = (person or {}).get("uid") or ""
    name = (person or {}).get("name") or ""
    if uid and name:
        return f"@[{uid}:{name}]"
    if name:
        return f"@{name}"
    return "反馈人未知"


def format_change(c):
    num = c.get("number", "?")
    title = c.get("title", "")
    url = c.get("url", "")
    notify = c.get("notify") or {}
    status = c.get("status") or c.get("state") or ""

    if notify.get("audience") == "feedbacker":
        people = notify.get("feedbackers") or []
        if people:
            targets = " ".join(mention(p) for p in people)
        else:
            targets = "反馈人未知"
        reason = notify.get("reason", "")
        result = "已完成/已关闭" if reason in {"closed", "status/done"} else "已关闭为 wontfix"
        return f"{targets} [产品管家] 闭环通知：需求池 issue #{num} {result}。\n标题：{title}\n链接：{url}"

    if notify.get("audience") == "product-steward":
        return f"[产品管家] 需求池 issue #{num} 状态有更新：{status}\n标题：{title}\n链接：{url}"

    # New or generic changes should stay concise; product steward may choose to send only if useful.
    return f"[产品管家] 需求池 issue #{num} 有更新：{status}\n标题：{title}\n链接：{url}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--changes", required=True, help="JSON array from scan_issues.py")
    ap.add_argument("--bot", default="产品管家")
    ap.add_argument("--examiner-uid", default="", help="deprecated; do not use as default feedbacker")
    args = ap.parse_args()

    changes = json.loads(args.changes)
    if not changes:
        return

    messages = [format_change(c) for c in changes if c.get("notify")]
    if not messages:
        return
    print("\n\n".join(messages))


if __name__ == "__main__":
    main()
