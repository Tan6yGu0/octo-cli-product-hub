#!/usr/bin/env python3
"""从目标仓库源码重建知识库（骨架，后续填充）。
用法: python3 scripts/build_kb.py --target ./octo-cli-target --kb ./kb
"""
import argparse, os, sys

DOMAINS = {
    "auth": ["cmd/auth.go", "internal/credential/", "internal/authstore/"],
    "config": ["internal/config/config.go", "cmd/config.go"],
    "transport": ["internal/client/"],
    "output": ["internal/output/"],
    "flags": ["cmd/root.go"],
    "domain": ["README.md", "CLAUDE.md"],
    "install": ["install.sh", ".goreleaser.yaml", "npm/", "Makefile"],
    "security": ["SECURITY.md", "internal/authstore/"],
    "skills": ["cmd/skills.go", "skills/"],
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="./octo-cli-target")
    ap.add_argument("--kb", default="./kb")
    args = ap.parse_args()

    print(f"Knowledge base builder — target: {args.target}, kb: {args.kb}")
    print(f"Domains: {list(DOMAINS.keys())}")
    print("TODO: extract key facts with line numbers from source files")

if __name__ == "__main__":
    main()
