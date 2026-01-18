#!/bin/sh

# Make sure venv is instantiated before first run
uv sync

# If GitHub CLI is installed then create a temporary token store used for gh auth.
if command -v gh >/dev/null 2>&1 && gh auth token >/dev/null 2>&1; then
    echo "$(gh auth token)" > .devcontainer/gh_token.txt;
fi

# If GEMINI_API_KEY present on host, create a temporary key store (deleted after run).
if [ -n \"${GEMINI_API_KEY}\" ]; then 
    echo ${GEMINI_API_KEY} > .devcontainer/gemini_key.txt;
fi
