#!/usr/bin/env python3
"""PRD linter：检查 PRD 文件是否包含禁止的技术实现细节。
用法: python3 scripts/lint_prd.py docs/prd/some-prd.md
"""
import argparse, re, sys

FORBIDDEN = [
    (r'\bRedis\b', "禁止提及 Redis"),
    (r'\b数据库表\b', "禁止提及数据库表"),
    (r'接口返回\s*200', "禁止提及接口返回200"),
    (r'HTTP\s*200', "禁止提及 HTTP 200"),
    (r'\bSQL\b', "禁止提及 SQL"),
    (r'\b缓存\b', "禁止提及缓存"),
    (r'```', "禁止使用代码块"),
    (r'技术方案', "PRD 只写 What 不写 How，禁止'技术方案'"),
]

FORBIDDEN_FIELDS = [
    r'内部字段名',
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="PRD markdown file to lint")
    args = ap.parse_args()

    with open(args.file) as f:
        content = f.read()

    errors = []
    for pattern, msg in FORBIDDEN:
        matches = list(re.finditer(pattern, content))
        if matches:
            for m in matches:
                line_num = content[:m.start()].count('\n') + 1
                errors.append(f"L{line_num}: {msg} (匹配: {m.group()})")

    if errors:
        print(f"❌ {args.file}: {len(errors)} 个问题")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print(f"✅ {args.file}: 通过")

if __name__ == "__main__":
    main()
