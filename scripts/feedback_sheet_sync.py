#!/usr/bin/env python3
"""Sync FDE/octo-cli feedback records to an Octo Docs spreadsheet.

This script is intentionally small and append/update oriented:
- source of truth remains GitHub issue + Loop task + runs/feedback-ledger.jsonl;
- the spreadsheet is the human-readable product feedback ledger;
- upsert key is feedback_seq in column A;
- all backend octo-cli calls MUST use --bot-id for this product steward bot.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from typing import Any

DEFAULT_BOT_ID = "286xqdrbrou92265c5d_bot"
DEFAULT_DOC_ID = "d_a47749dd0a79f2f2e2528f4e"
DEFAULT_CONFIG = "config/fde_channels.json"
DEFAULT_SHEET = "default"

HEADERS = [
    "反馈编号", "创建时间", "反馈人", "反馈人 UID", "来源会话类型", "来源会话 ID", "来源会话名称",
    "反馈原文", "反馈摘要", "类型", "优先级", "模块 Area", "是否已确认归档",
    "GitHub Issue", "Loop 任务", "当前状态", "PM/专家结论", "处理方案", "验收标准",
    "Workaround", "负责人/专家团", "最近进展", "下一步", "用户侧已通知阶段",
    "最后回告时间", "关闭时间", "备注",
]

WIDTHS = [
    110, 150, 100, 250, 110, 280, 180,
    320, 320, 120, 90, 160, 130,
    170, 220, 130, 260, 300, 260,
    240, 160, 320, 260, 150,
    160, 160, 260,
]


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    npm_bin = str(pathlib.Path.home() / ".npm-global" / "bin")
    env["PATH"] = npm_bin + os.pathsep + env.get("PATH", "")
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        print("COMMAND FAILED:", " ".join(cmd), file=sys.stderr)
        if r.stdout:
            print("STDOUT:\n" + r.stdout, file=sys.stderr)
        if r.stderr:
            print("STDERR:\n" + r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    return r


def load_json_file(path: str, default: Any) -> Any:
    p = pathlib.Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_payload(spec: str) -> dict[str, Any]:
    if spec == "-":
        return json.load(sys.stdin)
    stripped = spec.lstrip()
    if stripped.startswith("{"):
        return json.loads(spec)
    p = pathlib.Path(spec)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(spec)


def active_identity(bot_id: str) -> dict[str, Any]:
    out = run(["octo-cli", "auth", "status", "--bot-id", bot_id, "--format", "json"]).stdout
    data = json.loads(out).get("data") or {}
    active = data.get("active") or {}
    if active.get("robot_id") != bot_id:
        raise SystemExit(f"auth identity mismatch: expected {bot_id}, got {active.get('robot_id')}")
    return active


def docs_get(doc_id: str, bot_id: str) -> dict[str, Any]:
    out = run(["octo-cli", "docs", "get", doc_id, "--bot-id", bot_id, "--format", "json"]).stdout
    data = json.loads(out).get("data") or {}
    doc_type = data.get("docType") or data.get("doc_type")
    if str(doc_type).lower() != "sheet":
        raise SystemExit(f"unsupported doc type for feedback ledger: {doc_type}")
    return data


def sheet_get(doc_id: str, bot_id: str) -> dict[str, Any]:
    out = run(["octo-cli", "docs", "sheet", "get", doc_id, "--bot-id", bot_id, "--format", "json"]).stdout
    return json.loads(out).get("data") or {}


def cell_text(cells: dict[str, Any], sheet: str, row: int, col: int) -> str:
    val = cells.get(f"{sheet}!{row}:{col}") or {}
    return str(val.get("v") or "")


def parse_cell_key(key: str) -> tuple[str, int, int] | None:
    try:
        sheet, pos = key.split("!", 1)
        r, c = pos.split(":", 1)
        return sheet, int(r), int(c)
    except Exception:
        return None


def find_row(cells: dict[str, Any], sheet: str, feedback_seq: str) -> int | None:
    if not feedback_seq:
        return None
    for key, cell in cells.items():
        parsed = parse_cell_key(key)
        if not parsed:
            continue
        s, row, col = parsed
        if s == sheet and col == 0 and str((cell or {}).get("v") or "") == feedback_seq:
            return row
    return None


def next_row(cells: dict[str, Any], sheet: str) -> int:
    # The initial manual setup may leave a placeholder/example row at row 1.
    # Reuse it for the first real feedback record instead of treating it as data.
    if cell_text(cells, sheet, 1, 0).startswith("示例："):
        return 1
    max_row = 0
    for key in cells:
        parsed = parse_cell_key(key)
        if parsed and parsed[0] == sheet:
            max_row = max(max_row, parsed[1])
    return max(1, max_row + 1)


def source_type_label(value: Any) -> str:
    try:
        n = int(value or 0)
    except Exception:
        n = 0
    return {1: "DM", 2: "群", 5: "子区"}.get(n, str(value or ""))


def github_cell(p: dict[str, Any]) -> str:
    issue = p.get("issue") or p.get("github_issue_number")
    url = p.get("url") or p.get("github_issue_url")
    if issue and url:
        return f"#{issue} {url}"
    if issue:
        return f"#{issue}"
    return str(url or "")


def loop_cell(p: dict[str, Any]) -> str:
    key = p.get("loop_task_key") or p.get("loop_identifier") or ""
    task_id = p.get("loop_task_id") or ""
    if key and task_id:
        return f"{key} / {task_id}"
    return str(key or task_id or "")


def first_present(p: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in p and p[key] not in (None, ""):
            return p[key]
    return default


def build_row_map(p: dict[str, Any], *, append: bool) -> dict[int, str | None]:
    """Return column values. None means preserve existing cell on update."""
    def val(*keys: str, default: str = "") -> str | None:
        found = first_present(p, *keys, default=None)
        if found is not None:
            return str(found)
        return default if append else None

    status = first_present(p, "status", "current_status", default=("new" if append else None))
    recent = first_present(p, "recent_progress", default=("已归档到 GitHub issue，并创建/关联 Loop 父任务。" if append else None))
    next_step = first_present(p, "next_step", default=("等待 PM/专家团处理或状态变化。" if append else None))
    owner_team = first_present(p, "owner_team", "loop_assignee_id", default=("octo-cli 产品反馈闭环专家团" if append else None))
    confirmed = first_present(p, "confirmed", default=("是" if append else None))
    notified = first_present(p, "user_notified_stage", default=("none" if append else None))
    source_type = source_type_label(p.get("source_channel_type")) if (append or p.get("source_channel_type") not in (None, "")) else None
    github = github_cell(p)
    loop = loop_cell(p)
    row = [
        val("feedback_seq"),
        val("time", "created_at"),
        val("feedbacker"),
        val("feedbacker_uid"),
        source_type,
        val("source_channel_id"),
        val("source_channel_name"),
        val("feedback_body", "body"),
        val("title", "summary"),
        val("type"),
        val("priority"),
        val("area"),
        str(confirmed) if confirmed is not None else None,
        github if (append or github) else None,
        loop if (append or loop) else None,
        str(status) if status is not None else None,
        val("pm_expert_conclusion"),
        val("solution"),
        val("acceptance_criteria"),
        val("workaround"),
        str(owner_team) if owner_team is not None else None,
        str(recent) if recent is not None else None,
        str(next_step) if next_step is not None else None,
        str(notified) if notified is not None else None,
        val("last_user_notify_time"),
        val("closed_at"),
        val("note"),
    ]
    return {i: v for i, v in enumerate(row)}


def make_edit(sheet_data: dict[str, Any], payload: dict[str, Any], sheet: str) -> tuple[dict[str, Any], int, str]:
    cells = sheet_data.get("sheetCells") or {}
    feedback_seq = str(payload.get("feedback_seq") or "")
    row = find_row(cells, sheet, feedback_seq)
    action = "update"
    if row is None:
        row = next_row(cells, sheet)
        action = "append"

    edit_cells: dict[str, Any] = {}
    dims: dict[str, Any] = {}

    # Ensure header row is present/consistent. Only touches row 0.
    for col, header in enumerate(HEADERS):
        if cell_text(cells, sheet, 0, col) != header:
            edit_cells[f"{sheet}!0:{col}"] = {"v": header}
    for col, width in enumerate(WIDTHS):
        dims[f"c{col}"] = width

    for col, value in build_row_map(payload, append=(action == "append")).items():
        if value is not None:
            edit_cells[f"{sheet}!{row}:{col}"] = {"v": value}

    body: dict[str, Any] = {"cells": edit_cells}
    if dims:
        body["dims"] = dims
    return body, row, action


def sheet_edit(doc_id: str, bot_id: str, base_version: str, body: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as f:
        json.dump(body, f, ensure_ascii=False)
        path = f.name
    try:
        return run([
            "octo-cli", "docs", "sheet", "edit", doc_id,
            "--bot-id", bot_id,
            "--base-version", base_version,
            "--data", f"@{path}",
            "--format", "json",
        ], check=False)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def sync_once(doc_id: str, bot_id: str, payload: dict[str, Any], sheet: str, *, dry_run: bool) -> dict[str, Any]:
    docs_get(doc_id, bot_id)
    sheet_data = sheet_get(doc_id, bot_id)
    body, row, action = make_edit(sheet_data, payload, sheet)
    if dry_run:
        return {"ok": True, "dry_run": True, "action": action, "row": row, "edit": body}
    r = sheet_edit(doc_id, bot_id, sheet_data.get("baseVersion") or "", body)
    if r.returncode != 0 and ("base_version" in (r.stderr or "") or "412" in (r.stderr or "")):
        # Re-read and rebuild exactly once on optimistic-concurrency conflict.
        sheet_data = sheet_get(doc_id, bot_id)
        body, row, action = make_edit(sheet_data, payload, sheet)
        r = sheet_edit(doc_id, bot_id, sheet_data.get("baseVersion") or "", body)
    if r.returncode != 0:
        return {"ok": False, "action": action, "row": row, "returncode": r.returncode, "stderr_tail": (r.stderr or "")[-800:]}
    return {"ok": True, "action": action, "row": row, "result": json.loads(r.stdout or "{}")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True, help="JSON object, file path, or '-' for stdin")
    ap.add_argument("--doc-id", default=os.environ.get("FDE_FEEDBACK_SHEET_DOC_ID", ""))
    ap.add_argument("--bot-id", default=os.environ.get("FDE_OCTO_BOT_ID", DEFAULT_BOT_ID))
    ap.add_argument("--config", default=os.environ.get("FDE_CHANNEL_CONFIG", DEFAULT_CONFIG))
    ap.add_argument("--sheet", default=DEFAULT_SHEET)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = load_json_file(args.config, {})
    feedback_sheet = cfg.get("feedback_sheet") or {}
    doc_id = args.doc_id or feedback_sheet.get("doc_id") or DEFAULT_DOC_ID
    if not doc_id:
        print(json.dumps({"ok": False, "error": "missing_doc_id"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)

    active = active_identity(args.bot_id)
    payload = load_payload(args.payload)
    result = sync_once(doc_id, args.bot_id, payload, args.sheet, dry_run=args.dry_run)
    result.update({"doc_id": doc_id, "bot_id": args.bot_id, "profile": active.get("profile"), "api_base_url": active.get("api_base_url")})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
