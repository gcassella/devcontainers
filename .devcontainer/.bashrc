# Persistent history
export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history

# Fzf hotkeys
eval "$(fzf --bash)"

# Activate environment
uv sync && source .venv/bin/activate