#!/usr/bin/env bash
set -euo pipefail
if ! command -v pacman-conf >/dev/null 2>&1 || ! pacman-conf --repo-list | grep -Fxq multilib; then
    echo 'The desktop profile requires the Arch multilib repository for lib32-mesa. Enable multilib in /etc/pacman.conf and synchronize the system explicitly before retrying.' >&2
    exit 1
fi
