#!/usr/bin/env python3
"""校验知识库中的引用是否存在且行号正确。
用法: python3 scripts/verify_citations.py [--target ./octo-cli-target] [--kb ./kb]
"""
import argparse, os, re, sys

CITATION_RE = re.compile(r'来源:\s*(\S+#L\d+(?:-L\d+)?)')

def check_citation(citation, target_dir):
    # 格式: path#L10-L20
    if '#' not in citation:
        return False, f"malformed: {citation}"
    path, line_part = citation.rsplit('#', 1)
    full_path = os.path.join(target_dir, path)
    if not os.path.isfile(full_path):
        return False, f"file not found: {path}"
    m = re.match(r'L(\d+)(?:-L(\d+))?$', line_part)
    if not m:
        return False, f"bad line spec: {line_part}"
    start = int(m.group(1))
    end = int(m.group(2)) if m.group(2) else start
    with open(full_path) as f:
        lines = f.readlines()
    if start < 1 or start > len(lines):
        return False, f"start line {start} out of range (file has {len(lines)} lines)"
    if end < start or end > len(lines):
        return False, f"end line {end} out of range"
    return True, f"OK {citation} ({end - start + 1} lines)"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="./octo-cli-target", help="target repo clone dir")
    ap.add_argument("--kb", default="./kb", help="knowledge base dir")
    args = ap.parse_args()

    errors = 0
    checked = 0
    for fname in sorted(os.listdir(args.kb)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(args.kb, fname)
        with open(fpath) as f:
            for line_num, line in enumerate(f, 1):
                for m in CITATION_RE.finditer(line):
                    citation = m.group(1)
                    ok, msg = check_citation(citation, args.target)
                    checked += 1
                    status = "✅" if ok else "❌"
                    print(f"{status} {fname}:{line_num} {msg}")
                    if not ok:
                        errors += 1

    print(f"\n{checked} citations checked, {errors} errors")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
