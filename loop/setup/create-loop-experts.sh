#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   WORKSPACE_ID=<uuid> RUNTIME_REF_JSON='{"owner_id":"...","daemon_id":"...","provider":"openclaw"}' bash loop/setup/create-loop-experts.sh
#
# Prerequisites:
#   octo-cli auth must be valid for Loop API.
#   Discover workspace/runtime with:
#     octo-cli loop workspace list --format json
#     octo-cli loop runtime list --workspace-id "$WORKSPACE_ID" --format json

: "${WORKSPACE_ID:?set WORKSPACE_ID}"
: "${RUNTIME_REF_JSON:?set RUNTIME_REF_JSON}"

create_expert() {
  local name="$1"
  local desc_file="$2"
  jq -n --arg name "$name" --rawfile description "$desc_file" --argjson runtime_ref "$RUNTIME_REF_JSON" \
    '{name:$name, description:$description, runtime_ref:$runtime_ref}' \
    | octo-cli loop expert create --workspace-id "$WORKSPACE_ID" --data @- --format json
}

PRODUCT_JSON=$(create_expert "octo-cli 产品管家" "loop/experts/product-steward.md")
GITHUB_JSON=$(create_expert "octo-cli GitHub 专家" "loop/experts/github-expert.md")
PM_JSON=$(create_expert "octo-cli PM 专家" "loop/experts/pm-expert.md")

PRODUCT_ID=$(echo "$PRODUCT_JSON" | jq -r '.data.id // .data.expert_id // .id')
GITHUB_ID=$(echo "$GITHUB_JSON" | jq -r '.data.id // .data.expert_id // .id')
PM_ID=$(echo "$PM_JSON" | jq -r '.data.id // .data.expert_id // .id')

TEAM_JSON=$(jq -n --arg name "octo-cli 产品反馈闭环专家团" --rawfile description "loop/squads/octo-cli-feedback-loop.md" --arg leader_expert_id "$PRODUCT_ID" \
  '{name:$name, description:$description, leader_expert_id:$leader_expert_id}' \
  | octo-cli loop expert-team create --workspace-id "$WORKSPACE_ID" --data @- --format json)
TEAM_ID=$(echo "$TEAM_JSON" | jq -r '.data.id // .data.expert_team_id // .id')

jq -n --arg member_type expert --arg member_id "$GITHUB_ID" --arg role "github-executor" \
  '{member_type:$member_type, member_id:$member_id, role:$role}' \
  | octo-cli loop expert-team member add "$TEAM_ID" --workspace-id "$WORKSPACE_ID" --data @- --format json >/dev/null

jq -n --arg member_type expert --arg member_id "$PM_ID" --arg role "pm" \
  '{member_type:$member_type, member_id:$member_id, role:$role}' \
  | octo-cli loop expert-team member add "$TEAM_ID" --workspace-id "$WORKSPACE_ID" --data @- --format json >/dev/null

jq -n \
  --arg product "$PRODUCT_ID" \
  --arg github "$GITHUB_ID" \
  --arg pm "$PM_ID" \
  --arg team "$TEAM_ID" \
  '{product_steward_expert_id:$product, github_expert_id:$github, pm_expert_id:$pm, expert_team_id:$team}' \
  | tee loop/setup/created-loop-experts.json
