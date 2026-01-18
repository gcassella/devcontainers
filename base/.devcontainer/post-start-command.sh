#!/bin/sh

# [SYNC: ghcli]
# If GitHub CLI is authorized on host, read temporary token store and auth in container.
if [ -f .devcontainer/gh_token.txt ]; then
    # Auth with token passed in by init-command.sh
    cat .devcontainer/gh_token.txt | gh auth login --with-token

    # Delete gh_token.txt to prevent any accidental leakage.
    rm .devcontainer/gh_token.txt;
else
    echo "gh CLI auth not found on host, skipping auto-login.";
fi
# [/SYNC: ghcli]

# [SYNC: gemini]
# If GEMINI_API_KEY present on host, read API key and store in the container
if [ -f .devcontainer/gemini_key.txt ]; then 
    mv .devcontainer/gemini_key.txt /root/.gemini_key
    chmod 600 /root/.gemini_key
    echo "export GEMINI_API_KEY=$(cat /root/.gemini_key)" >> /root/.bashrc; 
else
    echo "No Gemini key found on host."; 
fi

# This is a temporary hack to fix the Gemini CLI Companion IDE integration
# until e.g. https://github.com/google-gemini/gemini-cli/pull/15049 is merged.
if [ -f /.dockerenv ]; then
    rm /.dockerenv;
fi

if [ -f /run/.containerenv ]; then
    rm /run/.containerenv;
fi
# [/SYNC: gemini]
