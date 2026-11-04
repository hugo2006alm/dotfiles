#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/shade-raid"
VENV_DIR="$DATA_DIR/venv"
BIN_DIR="$HOME/.local/bin"
CLI_PATH="$BIN_DIR/dotfiles"

if [[ "$DATA_DIR" != /* ]]; then
    echo 'XDG_DATA_HOME must be an absolute path.' >&2
    exit 1
fi
if (( $# > 1 )) || { (( $# == 1 )) && [[ "$1" != --preflight ]]; }; then
    echo 'Usage: install-cli.sh [--preflight]' >&2
    exit 2
fi

# Refuse conflicts before creating a venv or modifying a personal executable.
if [[ -e "$CLI_PATH" || -L "$CLI_PATH" ]]; then
    if [[ ! -L "$CLI_PATH" ]] || [[ "$(readlink -- "$CLI_PATH")" != "$VENV_DIR/bin/dotfiles" ]]; then
        echo "Refusing to overwrite existing $CLI_PATH. Move it aside explicitly, then retry." >&2
        exit 1
    fi
fi

if [[ "${1:-}" == --preflight ]]; then
    echo 'CLI destination preflight passed.'
    exit 0
fi

python -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check -e "$PROJECT_ROOT"
mkdir -p -- "$BIN_DIR"
if [[ ! -L "$CLI_PATH" ]]; then
    ln -s -- "$VENV_DIR/bin/dotfiles" "$CLI_PATH"
fi
printf 'CLI installed: %s\n' "$CLI_PATH"
