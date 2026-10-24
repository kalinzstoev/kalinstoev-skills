# eBay Lister — dev container

Claude Code, Node and Python run inside a Docker container. Only this folder is shared
with the container (at `/workspace`), so nothing else on your PC is touched.

## One-time setup (Windows)

1. In an **admin** PowerShell: `wsl --install`, then reboot.
2. Install Docker Desktop: `winget install -e --id Docker.DockerDesktop`, start it and accept its terms.

## Start working

From this folder:

```
docker compose up -d --build      # start the container in the background (stays running)
docker compose exec dev bash      # open a shell inside it; repeat for more terminals
docker compose stop               # stop it when you're done (start again with "up -d")
```

`docker compose ps` shows whether it's running. It also appears under Containers in Docker Desktop.

The first time, inside the container:

```
bash scripts/setup-skills.sh   # installs the project's skills into .claude/skills (list in the script)
claude                         # first run asks you to log in
```

Your Claude login is kept in the `claude-home` Docker volume, so you only log in once.

**VS Code alternative:** install the "Dev Containers" extension, open this folder and choose
"Reopen in Container". Skills are installed automatically.

## Secrets

Put eBay / API keys in a `.env` file here (it's git-ignored). They are passed into the container.
