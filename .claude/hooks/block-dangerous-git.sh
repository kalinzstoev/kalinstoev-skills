#!/bin/bash

INPUT=$(cat)
# Read the command with jq, else Python (a Windows host often has no jq). If neither
# works, check the raw hook input, so the block never silently switches off.
READ_COMMAND='import json, sys; print(json.load(sys.stdin)["tool_input"]["command"])'
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command' 2>/dev/null)
[ -z "$COMMAND" ] && COMMAND=$(echo "$INPUT" | python3 -c "$READ_COMMAND" 2>/dev/null)
[ -z "$COMMAND" ] && COMMAND=$(echo "$INPUT" | python -c "$READ_COMMAND" 2>/dev/null)
[ -z "$COMMAND" ] && COMMAND="$INPUT"

# A plain "git push" is allowed in this project; force pushes are still blocked.
DANGEROUS_PATTERNS=(
  "push .*(--force|-f( |\"|$))"
  "git reset --hard"
  "git clean -fd"
  "git clean -f"
  "git branch -D"
  "git checkout \."
  "git restore \."
  "reset --hard"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    echo "BLOCKED: '$COMMAND' matches dangerous pattern '$pattern'. The user has prevented you from doing this." >&2
    exit 2
  fi
done

exit 0
