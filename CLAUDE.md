# eBay Lister

## Goal

A small home tool: take several photos of an item and get it listed on my eBay account
as a **Buy It Now** listing with a good title, description, item specifics and price.
Volume is low (about 10–15 items in total), so favour simple and reliable over scalable.

Nothing is decided yet beyond that. Open questions include: how the price is set (sold
comps vs. Claude's estimate), whether I review each draft before it goes live (default:
yes, nothing posts without my approval), eBay API vs. bulk-upload spreadsheet, and
language (Python is installed). Settle these with `/grill-me` before writing code.

## Environment

- You are running inside a Docker dev container (`ebay-lister-dev`, Debian, user `node`).
  The project folder on my Windows PC is bind-mounted at `/workspace`; nothing else of
  the host is reachable.
- Installed: Node 24, Python 3 (+ pip, venv), git, jq, ImageMagick, Claude Code.
- Container config: `Dockerfile`, `docker-compose.yml`, `.devcontainer/`. If you change
  the Dockerfile, tell me to rebuild (`docker compose up -d --build` on the host); you
  can't rebuild from inside.
- Secrets (eBay keys, Anthropic API key) go in `.env` at the project root. It's
  git-ignored and passed into the container as environment variables. Never commit
  secrets or print them.

## eBay safety

- Develop and test against eBay's **Sandbox** environment with sandbox keys. Only switch
  to production when I say so.
- Never publish, revise or end a real listing without my explicit go-ahead for that item.

## Git

- Repo on `main`; commits are signed as me via repo-local config. Commit in small steps.
- A PreToolUse hook (`.claude/hooks/block-dangerous-git.sh`) blocks `git push`,
  `reset --hard`, `clean -f`, `branch -D`, `checkout .` / `restore .`. Don't try to work
  around it; ask me instead. I push myself.
- `core.filemode` is off (Windows bind mount shows every file as executable). Mark new
  scripts executable with `git update-index --chmod=+x <file>`.
- Line endings are LF for all text files (`.gitattributes`).

## Skills

Project skills live in `.claude/skills` and are installed by `scripts/setup-skills.sh`
(add new ones there, naming each skill explicitly): grill-me / grilling, research,
wizard, claude-api, git-guardrails-claude-code.

- `wizard` for steps only I can do (eBay developer account, keys, OAuth consent).
- `research` for eBay API facts — check primary eBay docs, don't rely on memory.
- `claude-api` before writing any code that calls Claude (e.g. describing photos).
