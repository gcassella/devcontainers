FROM gwmcassella/devcontainer-base:latest

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set UV_LINK_MODE=copy explicitly as we are running in a dev container and cannot
# hardlink files from the cache (in the container) to our .venv (in the host mount).
ENV UV_LINK_MODE=copy
