# [SYNC: common]
# Persistent history
export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history

# Fzf hotkeys
eval "$(fzf --bash)"

# Gemini API key
export GEMINI_API_KEY=$(cat /root/.gemini_key)

# Fix weird terminal issues.
export LC_CTYPE=en_US.UTF-8
export LC_ALL=en_US.UTF-8
# [/SYNC: common]

source .venv/bin/activate
