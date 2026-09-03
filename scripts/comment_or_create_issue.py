#!/usr/bin/env python3
"""产品管家闭环：查重后追加反馈，或创建新 issue，并记录 feedback-ledger。

示例：
python3 scripts/comment_or_create_issue.py \
  --query "message search app token" \
  --title "改进 message search 在 app_ token 下的错误提示" \
  --body body.md \
  --feedbacker "张三" \
  --type feature --priority P2 --area domain

默认不自动选择重复 issue；若传 --duplicate-number N 则追加到该 issue，否则创建新 issue。
"""
import argparse, json, os, subprocess, sys, datetime


def gh(*args, repo=None):
    cmd = ["gh"]
    if repo:
        cmd += ["--repo", repo]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    return r.stdout.strip()


def read_body(spec):
    if os.path.exists(spec):
        with open(spec) as f:
            return f.read()
    return spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Tan6yGu0/octo-cli-product-hub")
    ap.add_argument("--query", required=True, help="查重关键词，记录到 ledger")
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", required=True, help="正文字符串或文件路径")
    ap.add_argument("--feedbacker", required=True)
    ap.add_argument("--duplicate-number", type=int, help="若确认重复，追加到该 issue")
    ap.add_argument("--type", default="feature", choices=["bug", "feature", "docs", "question", "prd", "review"])
    ap.add_argument("--priority", default="P2", choices=["P0", "P1", "P2", "P3"])
    ap.add_argument("--area", default="unknown", choices=["auth", "config", "transport", "output", "flags", "domain", "install", "security", "skills", "unknown"])
    ap.add_argument("--source", default="octo-exam")
    ap.add_argument("--ledger", default="runs/feedback-ledger.jsonl")
    args = ap.parse_args()

    body = read_body(args.body)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if args.duplicate_number:
        comment = f"追加反馈人：{args.feedbacker}\n\n{body}"
        gh("issue", "comment", str(args.duplicate_number), "--body", comment, repo=args.repo)
        url = gh("issue", "view", str(args.duplicate_number), "--json", "url", "--jq", ".url", repo=args.repo)
        action = "commented"
        number = args.duplicate_number
    else:
        labels = [f"type/{args.type}", f"priority/{args.priority}", f"area/{args.area}", "status/new", f"source/{args.source}"]
        url = gh("issue", "create", "--title", args.title, "--body", body, "--label", ",".join(labels), repo=args.repo)
        action = "created"
        try:
            number = int(url.rstrip('/').split('/')[-1])
        except Exception:
            number = None

    os.makedirs(os.path.dirname(args.ledger), exist_ok=True)
    with open(args.ledger, "a") as f:
        f.write(json.dumps({
            "time": now,
            "action": action,
            "issue": number,
            "url": url,
            "query": args.query,
            "feedbacker": args.feedbacker,
            "title": args.title,
        }, ensure_ascii=False) + "\n")

    print(json.dumps({"action": action, "issue": number, "url": url}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
