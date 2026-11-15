# eBay Lister

## Goal

A small home tool: take several photos of an item and get it listed on my eBay account
as a **Buy It Now** listing with a good title, description, item specifics and price.
Volume is low (about 10–15 items in total), so favour simple and reliable over scalable.

The design is settled in `docs/design.md` (from a `/grill-me` session). Follow it, and
update it first if the plan changes.

The project is public (MIT). Keep the docs usable by someone who has never seen it: the
top-level `README.md` is for people using the skill, `.claude/skills/ebay-lister/README.md`
is the full walkthrough, `docs/dev-container.md` covers the optional container.

## Environment

- The project may be opened directly on the host or inside the optional Docker dev container
  (`ebay-lister-dev`, Debian, user `node`, project bind-mounted at `/workspace`). Check which
  before assuming tools or paths; the skill itself only needs Python 3.
- In the container: Node 24, Python 3 (+ pip, venv), git, jq, ImageMagick, Claude Code.
- Container config: `Dockerfile`, `docker-compose.yml`, `.devcontainer/`. If you change
  the Dockerfile, tell me to rebuild (`docker compose up -d --build` on the host); you
  can't rebuild from inside.
- Any secrets go in `.env` at the project root (git-ignored, passed into the container).
  None are needed right now. Never commit secrets or print them.

## eBay safety

- The tool never writes to my eBay account. Its only output is a drafts CSV that I upload
  myself, and every row's `Action` must be `Draft` (anything else could create a live listing).
- No eBay API calls and no eBay keys (agreed 2026-10-24); see `docs/design.md`.
- eBay UK is the default and the only tested site. Other sites work from the seller's own
  drafts template (`ebay-template.csv`); never guess a site's header values in code.
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

`ebay-lister` is this project's own skill, committed in `.claude/skills/ebay-lister`.
The other skills are third-party, installed into `.claude/skills` by
`scripts/setup-skills.sh` and git-ignored (add new ones there, naming each skill
explicitly): grill-me / grilling, research, wizard, claude-api, git-guardrails-claude-code.

- `wizard` for steps only I can do (eBay developer account, keys, OAuth consent).
- `research` for eBay API facts — check primary eBay docs, don't rely on memory.
- `claude-api` before writing any code that calls Claude (e.g. describing photos).
