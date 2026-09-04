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
import argparse, json, os, subprocess, sys, datetime, tempfile


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


def run(*args):
    r = subprocess.run(list(args), capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    return r.stdout.strip()


def read_body(spec):
    if os.path.exists(spec):
        with open(spec) as f:
            return f.read()
    return spec


def create_loop_task(*, workspace_id, title, description, assignee_id=""):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as f:
        f.write(description)
        desc_path = f.name
    try:
        cmd = [
            "octo-daemon", "--workspace-id", workspace_id,
            "issue", "create",
            "--title", title,
            "--description-file", desc_path,
            "--status", "todo",
            "--priority", "low",
        ]
        if assignee_id:
            cmd += ["--assignee-id", assignee_id]
        cmd += ["--output", "json"]
        out = run(*cmd)
        data = json.loads(out)
        return {
            "id": data.get("id") or data.get("issue", {}).get("id"),
            "identifier": data.get("identifier") or data.get("issue", {}).get("identifier"),
            "url": data.get("url") or data.get("web_url") or data.get("issue", {}).get("url") or data.get("issue", {}).get("web_url"),
            "raw": data,
        }
    finally:
        try:
            os.unlink(desc_path)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Tan6yGu0/octo-cli-product-hub")
    ap.add_argument("--query", required=True, help="查重关键词，记录到 ledger")
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", required=True, help="正文字符串或文件路径")
    ap.add_argument("--feedbacker", required=True)
    ap.add_argument("--feedbacker-uid", default="", help="Octo UID of original feedbacker, if known")
    ap.add_argument("--duplicate-number", type=int, help="若确认重复，追加到该 issue")
    ap.add_argument("--type", default="feature", choices=["bug", "feature", "docs", "question", "prd", "review"])
    ap.add_argument("--priority", default="P2", choices=["P0", "P1", "P2", "P3"])
    ap.add_argument("--area", default="unknown", choices=["auth", "config", "transport", "output", "flags", "domain", "install", "security", "skills", "unknown"])
    ap.add_argument("--source", default="octo-exam")
    ap.add_argument("--ledger", default="runs/feedback-ledger.jsonl")
    ap.add_argument("--create-loop-task", action="store_true", help="同时创建 Loop 父任务，并回写到 GitHub issue 评论和 ledger")
    ap.add_argument("--loop-workspace-id", default="bb4a2752-e52a-4f89-b768-ef1941ee68d2", help="Loop 工作区 ID，默认郭尘泽-FDE-exam")
    ap.add_argument("--loop-assignee-id", default="d8baa2b7-d80d-4128-af3b-fa65c2aa1f29", help="Loop 专家团/专家 UUID，默认 octo-cli 产品反馈闭环专家团")
    ap.add_argument("--feedback-seq", default="", help="稳定反馈序号，如 FDE-FB-005")
    args = ap.parse_args()

    body = read_body(args.body)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    loop_task = None

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

    if args.create_loop_task:
        seq_prefix = f"{args.feedback_seq}｜" if args.feedback_seq else ""
        loop_title = f"{seq_prefix}{args.title}"
        loop_desc = f"""# 产品反馈生命周期父任务

## GitHub 需求池
- Issue: #{number}
- URL: {url}

## 原始反馈人
- name: {args.feedbacker}
- uid: {args.feedbacker_uid or '未识别'}

## 反馈序号
- feedback_seq: {args.feedback_seq or '未指定'}

## 反馈内容
{body}

## 处理要求
- 该 Loop 父任务跟踪本条反馈从归档、PM/QC、实现/关闭到用户闭环的完整生命周期。
- 未完成对原始反馈人的最终闭环前，不得标记 done。
- 管理状态发负责人反馈专区，用户最终闭环回原群 @ 原始反馈人。
"""
        loop_task = create_loop_task(
            workspace_id=args.loop_workspace_id,
            title=loop_title,
            description=loop_desc,
            assignee_id=args.loop_assignee_id,
        )
        if loop_task.get("id"):
            run("octo-daemon", "--workspace-id", args.loop_workspace_id, "issue", "metadata", "set", loop_task["id"], "--key", "github_issue_url", "--value", url, "--type", "string")
            if number is not None:
                run("octo-daemon", "--workspace-id", args.loop_workspace_id, "issue", "metadata", "set", loop_task["id"], "--key", "github_issue_number", "--value", str(number), "--type", "number")
            run("octo-daemon", "--workspace-id", args.loop_workspace_id, "issue", "metadata", "set", loop_task["id"], "--key", "feedback_seq", "--value", args.feedback_seq or "未指定", "--type", "string")
            run("octo-daemon", "--workspace-id", args.loop_workspace_id, "issue", "metadata", "set", loop_task["id"], "--key", "feedbacker_name", "--value", args.feedbacker, "--type", "string")
            if args.feedbacker_uid:
                run("octo-daemon", "--workspace-id", args.loop_workspace_id, "issue", "metadata", "set", loop_task["id"], "--key", "feedbacker_uid", "--value", args.feedbacker_uid, "--type", "string")
        loop_note = (
            "Loop 父任务已创建/关联：\n"
            f"- loop_task_id: {loop_task.get('id')}\n"
            f"- loop_task_key: {loop_task.get('identifier')}\n"
            f"- loop_task_title: {loop_title}\n"
            f"- feedback_seq: {args.feedback_seq or '未指定'}\n"
            f"- feedbacker_name: {args.feedbacker}\n"
            f"- feedbacker_uid: {args.feedbacker_uid or '未识别'}"
        )
        gh("issue", "comment", str(number), "--body", loop_note, repo=args.repo)

    os.makedirs(os.path.dirname(args.ledger), exist_ok=True)
    with open(args.ledger, "a") as f:
        f.write(json.dumps({
            "time": now,
            "action": action,
            "issue": number,
            "url": url,
            "query": args.query,
            "feedbacker": args.feedbacker,
            "feedbacker_uid": args.feedbacker_uid,
            "title": args.title,
            "feedback_seq": args.feedback_seq,
            "loop_task_id": loop_task.get("id") if loop_task else "",
            "loop_task_key": loop_task.get("identifier") if loop_task else "",
        }, ensure_ascii=False) + "\n")

    print(json.dumps({"action": action, "issue": number, "url": url, "loop_task": loop_task}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
