#!/usr/bin/env python3
"""在本仓库创建 issue，自动打 label。
用法: python3 scripts/create_issue.py --title "..." --body "..." --type bug --priority P1 --area auth
"""
import argparse, json, subprocess, sys

def gh(*args, repo=None):
    cmd = ["gh"]
    if repo:
        cmd += ["--repo", repo]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ERROR: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    return r.stdout.strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Tan6yGu0/octo-cli-product-hub")
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", required=True)
    ap.add_argument("--type", default="bug", choices=["bug","feature","docs","question","prd","review"])
    ap.add_argument("--priority", default="P2", choices=["P0","P1","P2","P3"])
    ap.add_argument("--area", default="unknown", choices=["auth","config","transport","output","flags","domain","install","security","skills","unknown"])
    ap.add_argument("--source", default="octo-exam", choices=["octo-exam","user-feedback","agent-detected"])
    args = ap.parse_args()

    labels = [
        f"type/{args.type}",
        f"priority/{args.priority}",
        f"area/{args.area}",
        "status/new",
        f"source/{args.source}",
    ]

    url = gh("issue", "create",
             "--title", args.title,
             "--body", args.body,
             "--label", ",".join(labels),
             repo=args.repo)
    print(f"Created: {url}")
    return url

if __name__ == "__main__":
    main()
