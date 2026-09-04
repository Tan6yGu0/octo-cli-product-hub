#!/usr/bin/env bash
set -euo pipefail

cd /home/mlclaw/.openclaw/workspace/octo-cli-product-hub

OWNER='@[0cb0e235d14443d88f8803f54e19faf4:郭尘泽]'

if ! git pull --ff-only --autostash >/tmp/octo_product_hub_scan_git.out 2>/tmp/octo_product_hub_scan_git.err; then
  err=$(tail -c 500 /tmp/octo_product_hub_scan_git.err | tr '\n' ' ')
  printf '%s [产品管家] 需求池扫描脚本异常：git pull 失败，已停止本轮扫描。%s\n' "$OWNER" "${err:+ 错误：$err}"
  exit 0
fi

if ! CHANGES=$(python3 scripts/scan_issues.py 2>/tmp/octo_product_hub_scan.err); then
  err=$(tail -c 500 /tmp/octo_product_hub_scan.err | tr '\n' ' ')
  printf '%s [产品管家] 需求池扫描脚本异常/可能限流：已停止本轮扫描，不做高频重试。%s\n' "$OWNER" "${err:+ 错误：$err}"
  exit 0
fi

if ! MSG=$(python3 scripts/report_to_octo.py --changes "$CHANGES" --scope owner 2>/tmp/octo_product_hub_report.err); then
  err=$(tail -c 500 /tmp/octo_product_hub_report.err | tr '\n' ' ')
  printf '%s [产品管家] 需求池扫描脚本异常：通知内容生成失败。%s\n' "$OWNER" "${err:+ 错误：$err}"
  exit 0
fi

if [ -n "$MSG" ]; then
  printf '%s\n' "$MSG"
else
  printf 'NO_REPLY\n'
fi
