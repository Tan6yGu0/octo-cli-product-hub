#!/usr/bin/env python3
"""产品反馈统一入口：GitHub 需求池 + Loop 父任务 + 专家团指派 + 回写 + ledger。

设计目标：给群内产品管家一个唯一可调用脚本，避免手工拆步骤时漏掉 Loop 指派/metadata/回写。

示例：
python3 scripts/product_feedback_intake.py \
  --query "loop task create workspace output" \
  --title "loop task create 成功后应输出 workspace name/id" \
  --body runs/tmp-feedback.md \
  --feedbacker "郭尘泽" \
  --feedbacker-uid "0cb0e235d14443d88f8803f54e19faf4" \
  --feedback-seq "FDE-FB-006" \
  --type feature --priority P2 --area output \
  --source user-feedback

重复 issue：
python3 scripts/product_feedback_intake.py ... --duplicate-number 3

演练不写入：
python3 scripts/product_feedback_intake.py ... --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
from typing import Any

DEFAULT_REPO = "Tan6yGu0/octo-cli-product-hub"
DEFAULT_LOOP_WORKSPACE_ID = "bb4a2752-e52a-4f89-b768-ef1941ee68d2"  # 郭尘泽-FDE-exam
DEFAULT_LOOP_SQUAD_ID = "d8baa2b7-d80d-4128-af3b-fa65c2aa1f29"      # octo-cli 产品反馈闭环专家团
DEFAULT_LEDGER = "runs/feedback-ledger.jsonl"


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        print("COMMAND FAILED:", " ".join(cmd), file=sys.stderr)
        if r.stdout:
            print("STDOUT:\n" + r.stdout, file=sys.stderr)
        if r.stderr:
            print("STDERR:\n" + r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    return r


def gh(*args: str, repo: str = DEFAULT_REPO) -> str:
    cmd = ["gh"]
    if repo:
        cmd += ["--repo", repo]
    cmd += list(args)
    return run(cmd).stdout.strip()


def octo(*args: str, workspace_id: str = DEFAULT_LOOP_WORKSPACE_ID) -> str:
    cmd = ["octo-daemon", "--workspace-id", workspace_id] + list(args)
    return run(cmd).stdout.strip()


def read_body(spec: str) -> str:
    p = pathlib.Path(spec)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return spec


def search_issues(query: str, *, repo: str, limit: int = 10) -> list[dict[str, Any]]:
    out = gh(
        "issue", "list",
        "--state", "all",
        "--search", query,
        "--limit", str(limit),
        "--json", "number,title,state,labels,url,updatedAt",
        repo=repo,
    )
    return json.loads(out or "[]")


def next_feedback_seq(ledger_path: str) -> str:
    max_n = 0
    p = pathlib.Path(ledger_path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            seq = str(obj.get("feedback_seq") or "")
            if seq.startswith("FDE-FB-"):
                try:
                    max_n = max(max_n, int(seq.rsplit("-", 1)[-1]))
                except ValueError:
                    pass
    return f"FDE-FB-{max_n + 1:03d}"


def create_or_comment_github_issue(args: argparse.Namespace, body: str) -> tuple[str, int, str]:
    if args.duplicate_number:
        comment = f"追加反馈人：{args.feedbacker}\n\n{body}"
        gh("issue", "comment", str(args.duplicate_number), "--body", comment, repo=args.repo)
        url = gh("issue", "view", str(args.duplicate_number), "--json", "url", "--jq", ".url", repo=args.repo)
        return "commented", int(args.duplicate_number), url

    labels = [
        f"type/{args.type}",
        f"priority/{args.priority}",
        f"area/{args.area}",
        "status/new",
        f"source/{args.source}",
    ]
    url = gh(
        "issue", "create",
        "--title", args.title,
        "--body", body,
        "--label", ",".join(labels),
        repo=args.repo,
    )
    number = int(url.rstrip("/").split("/")[-1])
    return "created", number, url


def create_loop_task(args: argparse.Namespace, body: str, issue_number: int, issue_url: str) -> dict[str, Any]:
    loop_title = f"{args.feedback_seq}｜{args.title}"
    loop_desc = f"""# 产品反馈生命周期父任务

## GitHub 需求池
- Issue: #{issue_number}
- URL: {issue_url}
- 标题：{args.title}

## 原始反馈人
- name: {args.feedbacker}
- uid: {args.feedbacker_uid or '未识别'}

## 反馈序号
- feedback_seq: {args.feedback_seq}

## 反馈内容
{body}

## 处理要求
- 该 Loop 父任务跟踪本条反馈从归档、PM/QC、实现/关闭到用户闭环的完整生命周期。
- 创建后必须已指派给 `octo-cli 产品反馈闭环专家团`，并出现 leader run；否则归档未完成。
- 未完成对原始反馈人的最终闭环前，不得标记 done。
- 管理状态发负责人反馈专区，用户最终闭环回原群 @ 原始反馈人。
"""
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as f:
        f.write(loop_desc)
        desc_path = f.name
    try:
        out = octo(
            "issue", "create",
            "--title", loop_title,
            "--description-file", desc_path,
            "--status", "todo",
            "--priority", "low",
            "--assignee-id", args.loop_assignee_id,
            "--output", "json",
            workspace_id=args.loop_workspace_id,
        )
    finally:
        try:
            os.unlink(desc_path)
        except OSError:
            pass

    data = json.loads(out)
    loop = {
        "id": data.get("id") or data.get("issue", {}).get("id"),
        "identifier": data.get("identifier") or data.get("issue", {}).get("identifier"),
        "title": loop_title,
        "assignee_id": data.get("assignee_id") or data.get("issue", {}).get("assignee_id"),
        "assignee_type": data.get("assignee_type") or data.get("issue", {}).get("assignee_type"),
        "raw": data,
    }
    if not loop["id"]:
        raise RuntimeError("Loop task created but id not found in response")

    # Durable metadata for future scanners/reruns.
    metadata = {
        "github_issue_url": (issue_url, "string"),
        "github_issue_number": (str(issue_number), "number"),
        "feedback_seq": (args.feedback_seq, "string"),
        "feedbacker_name": (args.feedbacker, "string"),
    }
    if args.feedbacker_uid:
        metadata["feedbacker_uid"] = (args.feedbacker_uid, "string")
    for key, (value, typ) in metadata.items():
        octo(
            "issue", "metadata", "set", loop["id"],
            "--key", key,
            "--value", value,
            "--type", typ,
            workspace_id=args.loop_workspace_id,
        )

    return loop


def wait_for_dispatch(args: argparse.Namespace, loop_id: str, timeout_sec: int) -> dict[str, Any]:
    deadline = time.time() + timeout_sec
    last_runs: list[dict[str, Any]] = []
    while True:
        out = octo("issue", "runs", loop_id, "--output", "json", workspace_id=args.loop_workspace_id)
        try:
            runs = json.loads(out or "[]")
        except Exception:
            runs = []
        last_runs = runs
        if runs:
            return {"dispatched": True, "runs": runs}
        if time.time() >= deadline:
            return {"dispatched": False, "runs": last_runs}
        time.sleep(2)


def append_ledger(args: argparse.Namespace, *, action: str, issue_number: int, issue_url: str, loop: dict[str, Any], dispatched: bool) -> None:
    p = pathlib.Path(args.ledger)
    p.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "time": dt.datetime.now(dt.timezone.utc).isoformat(),
        "action": action,
        "issue": issue_number,
        "url": issue_url,
        "query": args.query,
        "feedbacker": args.feedbacker,
        "feedbacker_uid": args.feedbacker_uid,
        "title": args.title,
        "feedback_seq": args.feedback_seq,
        "loop_task_id": loop.get("id"),
        "loop_task_key": loop.get("identifier"),
        "loop_assignee_id": args.loop_assignee_id,
        "loop_dispatched": dispatched,
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def comment_back_to_github(args: argparse.Namespace, *, issue_number: int, loop: dict[str, Any], dispatched: bool) -> None:
    note = f"""Loop 父任务已创建/关联：
- loop_task_id: {loop.get('id')}
- loop_task_key: {loop.get('identifier')}
- loop_task_title: {loop.get('title')}
- loop_assignee_id: {args.loop_assignee_id}
- loop_dispatched: {str(dispatched).lower()}
- feedback_seq: {args.feedback_seq}
- feedbacker_name: {args.feedbacker}
- feedbacker_uid: {args.feedbacker_uid or '未识别'}
"""
    gh("issue", "comment", str(issue_number), "--body", note, repo=args.repo)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--query", required=True, help="查重关键词，会先输出候选；不自动合并，除非传 --duplicate-number")
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", required=True, help="正文字符串或文件路径")
    ap.add_argument("--feedbacker", required=True)
    ap.add_argument("--feedbacker-uid", default="")
    ap.add_argument("--feedback-seq", default="", help="不填则根据 ledger 自动递增")
    ap.add_argument("--duplicate-number", type=int, help="若确认重复，追加到该 GitHub issue；否则新建")
    ap.add_argument("--type", default="feature", choices=["bug", "feature", "docs", "question", "prd", "review"])
    ap.add_argument("--priority", default="P2", choices=["P0", "P1", "P2", "P3"])
    ap.add_argument("--area", default="unknown", choices=["auth", "config", "transport", "output", "flags", "domain", "install", "security", "skills", "unknown"])
    ap.add_argument("--source", default="user-feedback", choices=["octo-exam", "user-feedback", "agent-detected"])
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--loop-workspace-id", default=DEFAULT_LOOP_WORKSPACE_ID)
    ap.add_argument("--loop-assignee-id", default=DEFAULT_LOOP_SQUAD_ID)
    ap.add_argument("--dispatch-timeout-sec", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    body = read_body(args.body)
    if not args.feedback_seq:
        args.feedback_seq = next_feedback_seq(args.ledger)

    candidates = search_issues(args.query, repo=args.repo, limit=10)
    plan = {
        "dry_run": args.dry_run,
        "query": args.query,
        "candidate_count": len(candidates),
        "candidates": candidates[:5],
        "action": "comment_existing" if args.duplicate_number else "create_new",
        "duplicate_number": args.duplicate_number,
        "feedback_seq": args.feedback_seq,
        "title": args.title,
        "labels": [f"type/{args.type}", f"priority/{args.priority}", f"area/{args.area}", "status/new", f"source/{args.source}"],
        "loop_workspace_id": args.loop_workspace_id,
        "loop_assignee_id": args.loop_assignee_id,
    }

    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    action, issue_number, issue_url = create_or_comment_github_issue(args, body)
    loop = create_loop_task(args, body, issue_number, issue_url)
    dispatch = wait_for_dispatch(args, loop["id"], args.dispatch_timeout_sec)
    dispatched = bool(dispatch.get("dispatched"))
    comment_back_to_github(args, issue_number=issue_number, loop=loop, dispatched=dispatched)
    append_ledger(args, action=action, issue_number=issue_number, issue_url=issue_url, loop=loop, dispatched=dispatched)

    result = {
        "ok": True,
        "action": action,
        "github_issue": {"number": issue_number, "url": issue_url, "title": args.title},
        "loop_task": loop,
        "loop_dispatched": dispatched,
        "run_count": len(dispatch.get("runs") or []),
        "management_summary": (
            f"管理汇总：已归档产品反馈。\n\n"
            f"- 原反馈人：{args.feedbacker}\n"
            f"- 处理：{'追加到既有需求' if args.duplicate_number else '查重后新建需求池 issue'} #{issue_number}，并创建/指派 Loop 父任务\n"
            f"- GitHub issue：#{issue_number}《{args.title}》\n"
            f"- Loop task：{loop.get('identifier')} / {loop.get('id')}\n"
            f"- Loop dispatched：{str(dispatched).lower()}\n"
            f"- feedback_seq：{args.feedback_seq}\n"
            f"- 类型：type/{args.type}\n"
            f"- 优先级：priority/{args.priority}\n"
            f"- 状态：status/new\n"
            f"- 领域：area/{args.area}\n"
            f"- 来源：source/{args.source}"
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
