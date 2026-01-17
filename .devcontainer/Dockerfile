######################
# NODE BUILDER IMAGE #
######################

FROM node:20-alpine AS nodebuilder

WORKDIR /build
RUN npm install -g @google/gemini-cli@preview

####################
# GO BUILDER IMAGE #
####################

FROM golang:1.25.6-alpine AS gobuilder

RUN go install github.com/walles/moor/v2/cmd/moor@latest

################
# BREW BUILDER #
################

FROM debian:trixie-slim AS brewbuilder

# Create a brewbuilder user as brew install script cannot run under root. Need
# a sudoer with a home directory.
ARG USERNAME=brewbuilder
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME
USER $USERNAME


# Install homebrew.
RUN sudo apt-get update \
    && sudo apt-get install build-essential procps curl file git -y

RUN NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
ENV PATH="/home/linuxbrew/.linuxbrew/bin:${PATH}"
RUN eval "$(brew shellenv)"

# Use homebrew to install Sapling.
RUN brew install sapling

USER root

##############
# MAIN IMAGE #
##############

FROM ghcr.io/astral-sh/uv:debian-slim

# Set UV_LINK_MODE=copy explicitly as we are running in a dev container and cannot
# hardlink files from the cache (in the container) to our .venv (in the host mount).
ENV UV_LINK_MODE=copy

# Copy Gemini CLI from Node builder stage
COPY --from=nodebuilder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=nodebuilder /usr/local/bin /usr/local/bin

# Copy Moor pager from Go builder stage.
COPY --from=gobuilder /go/bin/moor /usr/local/bin
ENV PAGER=moor

# Copy Homebrew installation from Brew builder stage (required for dynamic loader and libs).
COPY --from=brewbuilder /home/linuxbrew/.linuxbrew /home/linuxbrew/.linuxbrew
RUN ln -s /home/linuxbrew/.linuxbrew/bin/sl /usr/local/bin/sl

# Install dependencies and utilities.
RUN apt-get update && apt-get install -y --no-install-recommends \
  nodejs \
  make \
  python3 \
  g++ \
  man-db \
  curl \
  dnsutils \
  less \
  jq \
  bc \
  gh \
  git \
  unzip \
  rsync \
  ripgrep \
  procps \
  psmisc \
  lsof \
  socat \
  fzf \
  tmux \
  ca-certificates \
  openssl \
  openssh-client \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Persist bash history across dev container sessions.
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
    && echo "$SNIPPET" >> "/root/.bashrc"

# Set up fzf key bindings and fuzzy completion
RUN echo "eval \"\$(fzf --bash)\"" >> "/root/.bashrc"
