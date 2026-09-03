#!/usr/bin/env python3
"""群回报脚本：将 issue/PRD 变化格式化为群消息。
用法: python3 scripts/report_to_octo.py --changes '[...]' --bot product-steward --examiner-uid <uid>
"""
import argparse, json, sys

def format_message(changes, bot_name, examiner_uid):
    if not changes:
        print("（无变化，不发消息）", file=sys.stderr)
        sys.exit(0)

    lines = [f"@{examiner_uid} [{bot_name}] 扫描发现 {len(changes)} 条变化："]
    for c in changes:
        num = c.get("number", "?")
        title = c.get("title", "")
        ctype = c.get("type", "")
        labels = c.get("labels", [])
        status = next((l for l in labels if l.startswith("status/")), "unknown")
        lines.append(f"  #{num} [{ctype}] {title} ({status})")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--changes", required=True, help="JSON array of changes")
    ap.add_argument("--bot", default="产品管家", choices=["产品管家", "PM"])
    ap.add_argument("--examiner-uid", default="主考", help="主考 uid for @mention")
    args = ap.parse_args()

    changes = json.loads(args.changes)
    msg = format_message(changes, args.bot, args.examiner_uid)
    print(msg)

if __name__ == "__main__":
    main()
