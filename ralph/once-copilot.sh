#!/bin/bash
set -eo pipefail

issues=$(cat issues/*.md 2>/dev/null || echo "No issues found")
commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
prompt=$(cat ralph/prompt.md)

full_prompt=$(cat <<EOF
Previous commits:
$commits

Issues:
$issues

$prompt
EOF
)

copilot -i "$full_prompt"
