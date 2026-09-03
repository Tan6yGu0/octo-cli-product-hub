#!/usr/bin/env python3
"""PM 扫描：检查 PRD 和 review 相关 issue 状态变化。
用法: python3 scripts/pm_scan.py [--state-file runs/pm-scan-state.json]
"""
import argparse, json, os, subprocess, sys

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
    ap.add_argument("--state-file", default="runs/pm-scan-state.json")
    args = ap.parse_args()

    # 查 type/prd + type/review 的 issue
    issues = gh_json("issue", "list", "--state", "all",
                     "--json", "number,title,state,labels,updatedAt",
                     "--limit", "100", repo=args.repo)

    pm_issues = []
    for issue in issues:
        label_names = [l["name"] if isinstance(l, dict) else l for l in issue.get("labels", [])]
        if any(t in label_names for t in ["type/prd", "type/review"]):
            pm_issues.append({"number": issue["number"], "title": issue["title"],
                              "state": issue["state"], "labels": sorted(label_names),
                              "updatedAt": issue["updatedAt"]})

    seen = {}
    if os.path.exists(args.state_file):
        with open(args.state_file) as f:
            seen = {int(k): v for k, v in json.load(f).items()}

    changes = []
    for issue in pm_issues:
        num = issue["number"]
        if num not in seen or seen[num] != issue:
            changes.append({"number": num, "type": "new" if num not in seen else "changed", **issue})
        seen[num] = issue

    os.makedirs(os.path.dirname(args.state_file), exist_ok=True)
    with open(args.state_file, "w") as f:
        json.dump({str(k): v for k, v in seen.items()}, f, indent=2)

    if changes:
        print(json.dumps(changes, ensure_ascii=False, indent=2))
    else:
        print("[]")

if __name__ == "__main__":
    main()
