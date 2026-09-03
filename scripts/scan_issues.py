#!/usr/bin/env python3
"""扫描仓库 issue 变化，输出新增/变更列表。
用法: python3 scripts/scan_issues.py [--state-file runs/issue-scan-state.json]
"""
import argparse, json, os, subprocess, sys, datetime

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Tan6yGu0/octo-cli-product-hub")
    ap.add_argument("--state-file", default="runs/issue-scan-state.json")
    args = ap.parse_args()

    issues = gh_json("issue", "list", "--state", "all", "--json", "number,title,state,labels,updatedAt",
                     "--limit", "100", repo=args.repo)
    seen = {}
    if os.path.exists(args.state_file):
        with open(args.state_file) as f:
            seen = {int(k): v for k, v in json.load(f).items()}

    changes = []
    for issue in issues:
        num = issue["number"]
        label_names = [l["name"] if isinstance(l, dict) else l for l in issue.get("labels", [])]
        sig = {"title": issue["title"], "state": issue["state"], "labels": sorted(label_names), "updatedAt": issue["updatedAt"]}
        if num not in seen:
            changes.append({"number": num, "type": "new", **sig})
        elif seen[num] != sig:
            changes.append({"number": num, "type": "changed", **sig})
        seen[num] = sig

    os.makedirs(os.path.dirname(args.state_file), exist_ok=True)
    with open(args.state_file, "w") as f:
        json.dump({str(k): v for k, v in seen.items()}, f, indent=2)

    if changes:
        print(json.dumps(changes, ensure_ascii=False, indent=2))
    else:
        print("[]")

if __name__ == "__main__":
    main()
