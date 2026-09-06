#!/usr/bin/env bash
set -euo pipefail

cd /home/mlclaw/.openclaw/workspace/octo-cli-product-hub

OWNER='@[0cb0e235d14443d88f8803f54e19faf4:郭尘泽]'

if ! git pull --ff-only --autostash >/tmp/octo_product_hub_scan_git.out 2>/tmp/octo_product_hub_scan_git.err; then
  err=$(tail -c 500 /tmp/octo_product_hub_scan_git.err | tr '\n' ' ')
  printf '%s [产品管家] GitHub 暂时连接超时或不可用，本轮需求池扫描已跳过，等待下次定时扫描自动恢复。\n' "$OWNER"
  printf '%s ERROR git pull skipped scan; detail: %s\n' "$(date -Is)" "$err" >&2
  exit 0
fi

if ! CHANGES=$(python3 scripts/scan_issues.py 2>/tmp/octo_product_hub_scan.err); then
  err=$(tail -c 500 /tmp/octo_product_hub_scan.err | tr '\n' ' ')
  printf '%s [产品管家] GitHub 暂时连接超时或接口不可用，本轮需求池扫描已跳过，等待下次定时扫描自动恢复；不会高频重试刷接口。\n' "$OWNER"
  printf '%s ERROR issue scan skipped; detail: %s\n' "$(date -Is)" "$err" >&2
  exit 0
fi

if ! MSG=$(python3 scripts/report_to_octo.py --changes "$CHANGES" --scope owner 2>/tmp/octo_product_hub_report.err); then
  err=$(tail -c 500 /tmp/octo_product_hub_report.err | tr '\n' ' ')
  printf '%s [产品管家] 本轮需求池扫描结果生成失败，已跳过，等待下次定时扫描自动恢复。\n' "$OWNER"
  printf '%s ERROR report generation skipped; detail: %s\n' "$(date -Is)" "$err" >&2
  exit 0
fi

if [ -n "$MSG" ]; then
  printf '%s\n' "$MSG"
else
  printf 'NO_REPLY\n'
fi
