#!/bin/sh

# [SYNC: secrets]
# Clean up injected secrets in post-attach as initCommand may run on attach.
if [ -f .devcontainer/gh_token.txt ]; then
    # Delete gh_token.txt to prevent any accidental leakage.
    rm .devcontainer/gh_token.txt;
fi

if [ -f .devcontainer/gemini_key.txt ]; then 
    # Delete gemini_key.txt to prevent any accidental leakage.
    rm .devcontainer/gemini_key.txt;
fi
# [/SYNC: secrets]
