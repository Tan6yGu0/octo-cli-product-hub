#!/usr/bin/env python3
"""按关键词查重需求池 issue。
用法：python3 scripts/search_issues.py --query "message search app token" [--repo Tan6yGu0/octo-cli-product-hub]
"""
import argparse, json, subprocess, sys


def gh(*args, repo=None):
    cmd = ["gh"]
    if repo:
        cmd += ["--repo", repo]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Tan6yGu0/octo-cli-product-hub")
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", default="20")
    args = ap.parse_args()

    # gh issue list 的 --search 使用 GitHub issue search 语法。
    out = gh(
        "issue", "list",
        "--state", "all",
        "--search", args.query,
        "--limit", str(args.limit),
        "--json", "number,title,state,labels,url,updatedAt",
        repo=args.repo,
    )
    issues = json.loads(out or "[]")
    print(json.dumps(issues, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
