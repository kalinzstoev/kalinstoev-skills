# Dev container (optional)

You don't need this to use the skill. It is the setup the project was built in: Claude Code,
Node and Python run inside a Docker container, and only the project folder is shared with it
(at `/workspace`), so nothing else on your PC is touched.

## One-time setup (Windows)

1. In an **admin** PowerShell: `wsl --install`, then reboot.
2. Install Docker Desktop: `winget install -e --id Docker.DockerDesktop`, start it and accept
   its terms.

On macOS or Linux, install Docker Desktop or Docker Engine in the usual way.

## Start working

From the project folder:

```
docker compose up -d --build      # start the container in the background (stays running)
docker compose exec dev bash      # open a shell inside it; repeat for more terminals
docker compose stop               # stop it when you're done (start again with "up -d")
```

`docker compose ps` shows whether it's running. It also appears under Containers in Docker
Desktop.

The first time, inside the container:

```
bash scripts/setup-skills.sh   # installs the extra skills listed below
claude                         # first run asks you to log in
```

Your Claude login is kept in the `claude-home` Docker volume, so you only log in once.

**VS Code alternative:** install the "Dev Containers" extension, open the project folder and
choose "Reopen in Container". The extra skills are installed automatically.

## Extra skills

`scripts/setup-skills.sh` installs the third-party Claude Code skills that were used while
designing and building the project. They are not needed to list items, and they are not
committed here (`skills-lock.json` records where each one comes from):

- `grill-me` / `grilling`, `research`, `wizard`, `git-guardrails-claude-code` from
  [mattpocock/skills](https://github.com/mattpocock/skills)
- `claude-api` from [anthropics/skills](https://github.com/anthropics/skills)

The script needs Node (`npx`). The `ebaylister` skill itself is part of this repo.

## Secrets

None are needed. If that ever changes, they go in a `.env` file in the project root (it is
git-ignored and passed into the container).
