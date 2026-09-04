#!/usr/bin/env python3
"""Format issue/PRD changes for the single-entry product steward workflow.

This script only prints the message body; the caller decides where to send it.
Rules:
- Empty changes => print nothing and exit 0 (no message).
- Management notifications go to the owner feedback thread, not the main group.
- User closure notifications mention original feedbackers in the original group.
- User-facing closure text defaults to no issue URL; add trace links only on request.
- PM/GitHub/QC experts are background roles by default.
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


def format_change(c, owner, scope="owner"):
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
        if scope == "feedbacker":
            return f"{targets} [产品管家] 你反馈的「{title}」{result}。\n处理结果：已完成需求池闭环。需要追溯详情我可以再补 issue 编号/链接。"
        return f"{mention(owner)} [产品管家] 负责人同步：issue #{num} 已到用户闭环节点。\n标题：{title}\n原始反馈人：{targets}\n建议动作：由最长 Bot 回原群通知处理结果，默认不带链接。\n追溯：{url}"

    if notify.get("audience") == "product-steward":
        target = mention(owner)
        return f"{target} [产品管家] 负责人同步：需求池 issue #{num} 状态有更新：{status}\n标题：{title}\n链接：{url}"

    # New or generic GitHub scan changes are management status, not user-facing closure.
    target = mention(owner)
    return f"{target} [产品管家] 负责人同步：需求池 issue #{num} 有更新：{status}\n标题：{title}\n链接：{url}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--changes", required=True, help="JSON array from scan_issues.py")
    ap.add_argument("--bot", default="产品管家")
    ap.add_argument("--owner-name", default="郭尘泽", help="Owner/main examiner to notify for GitHub scan management status")
    ap.add_argument("--owner-uid", default="0cb0e235d14443d88f8803f54e19faf4", help="Owner Octo UID for GitHub scan management status")
    ap.add_argument("--scope", choices=["owner", "feedbacker"], default="owner", help="Format for fixed delivery target: owner feedback thread or original feedbacker group")
    args = ap.parse_args()

    changes = json.loads(args.changes)
    if not changes:
        return

    owner = {"name": args.owner_name, "uid": args.owner_uid}
    messages = [format_change(c, owner, args.scope) for c in changes if c.get("notify")]
    if not messages:
        return
    print("\n\n".join(messages))


if __name__ == "__main__":
    main()
