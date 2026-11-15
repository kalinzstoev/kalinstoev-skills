#!/usr/bin/env bash
# Installs the third-party Claude Code skills used to develop this project into
# .claude/skills (run from the project root). Not needed to use the ebaylister skill.
# Safe to re-run; skips repos whose skills are all present.
set -euo pipefail

# Usage: install <repo> <skill>...
install() {
  local repo=$1; shift
  for skill in "$@"; do
    if [ ! -d ".claude/skills/$skill" ]; then
      npx -y skills@latest add "$repo" --skill "$@" --agent claude-code --copy -y
      return
    fi
  done
}

# grill-me is a thin wrapper that calls the "grilling" skill, so both are needed
install mattpocock/skills grill-me grilling research wizard git-guardrails-claude-code
install anthropics/skills claude-api

# ebaylister is this project's own skill: it's committed in skills/, not installed here
