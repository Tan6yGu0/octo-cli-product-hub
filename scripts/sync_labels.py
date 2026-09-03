#!/usr/bin/env python3
"""同步 labels.yml 到 GitHub Issues。
依赖: gh CLI 已登录，或设置 GITHUB_TOKEN 环境变量。
用法: python3 scripts/sync_labels.py [--repo Tan6yGu0/octo-cli-product-hub] [--dry-run]
"""
import argparse, json, subprocess, sys, yaml

def gh(*args, repo=None):
    cmd = ["gh"]
    if repo:
        cmd += ["--repo", repo]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ERROR: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    return r.stdout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Tan6yGu0/octo-cli-product-hub")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open("labels.yml") as f:
        data = yaml.safe_load(f)

    existing = json.loads(gh("label", "list", "--json", "name", repo=args.repo))
    existing_names = {l["name"] for l in existing}

    for label in data["labels"]:
        name = label["name"]
        if name in existing_names:
            if args.dry_run:
                print(f"[DRY] UPDATE {name}")
            else:
                gh("label", "edit", name,
                   "--color", label["color"],
                   "--description", label.get("description", ""),
                   repo=args.repo)
                print(f"UPDATED {name}")
        else:
            if args.dry_run:
                print(f"[DRY] CREATE {name}")
            else:
                gh("label", "create", name,
                   "--color", label["color"],
                   "--description", label.get("description", ""),
                   repo=args.repo)
                print(f"CREATED {name}")

    print(f"Done: {len(data['labels'])} labels processed")

if __name__ == "__main__":
    main()
