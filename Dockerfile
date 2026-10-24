FROM node:24-bookworm

# Tools for the eBay lister: git, Python for scripting, image utilities for photos
RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl ca-certificates jq python3 python3-pip python3-venv imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Keep all Claude Code state (login, settings) in one dir, owned by "node" so the volume is writable
RUN mkdir -p /home/node/.claude && chown -R node:node /home/node/.claude
ENV CLAUDE_CONFIG_DIR=/home/node/.claude

# Run as the non-root "node" user that ships with the image
USER node
WORKDIR /workspace

# The bind-mounted project is owned by a different user ID, so tell git it's safe to use
RUN git config --global --add safe.directory /workspace

CMD ["bash"]
