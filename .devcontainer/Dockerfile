FROM mcr.microsoft.com/devcontainers/base:debian

# Install uv (The modern Python manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install OpenCode AI Agent
RUN curl -fsSL https://opencode.ai/install | bash

# Ensure the container stays running
CMD ["sleep", "infinity"]
