#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
setup_args=()
dry_run=false
upgrade_system=false
for argument in "$@"; do
    case "$argument" in
        --dry-run) dry_run=true ;;
        --upgrade-system) upgrade_system=true ;;
        --github|--ssh-server) setup_args+=("$argument") ;;
        -h|--help)
            echo 'Usage: bash scripts/bootstrap.sh [--dry-run] [--upgrade-system] [--github] [--ssh-server]'
            echo 'Run interactively as a normal Arch user. Login setup is a separate dotfiles setup-login command.'
            exit 0 ;;
        *) printf 'Unknown option: %s\n' "$argument" >&2; exit 2 ;;
    esac
done

if "$dry_run"; then
    echo 'PLAN: preflight CLI destination; install bootstrap packages'
    if "$upgrade_system"; then echo 'PLAN: perform explicitly requested full system upgrade'; fi
    echo 'PLAN: build yay in a private temporary directory if absent'
    echo 'PLAN: install CLI into a private Python venv; run dotfiles setup'
    printf 'Setup options: %s\n' "${setup_args[*]}"
    echo 'No changes applied. Login setup remains an explicit step.'
    exit 0
fi

if [[ ! -t 0 || ! -t 2 ]]; then
    echo 'Bootstrap requires an interactive terminal for authentication. Run it yourself.' >&2
    exit 1
fi
if (( EUID == 0 )); then
    echo 'Run bootstrap as a normal user, not root.' >&2
    exit 1
fi
if [[ ! -f /etc/arch-release ]]; then
    echo 'Bootstrap supports Arch Linux only.' >&2
    exit 1
fi

bash "$PROJECT_ROOT/scripts/install-cli.sh" --preflight
bash "$PROJECT_ROOT/scripts/check-desktop-prerequisites.sh"
if "$upgrade_system"; then
    sudo pacman -Syu --noconfirm
fi
sudo pacman -S --needed --noconfirm git base-devel python python-pip

if ! command -v yay >/dev/null 2>&1; then
    build_dir="$(mktemp -d -t shade-raid-yay.XXXXXXXXXX)"
    trap 'rm -rf -- "$build_dir"' EXIT
    git clone -- https://aur.archlinux.org/yay.git "$build_dir/yay"
    (cd -- "$build_dir/yay" && makepkg -si --noconfirm)
fi

bash "$PROJECT_ROOT/scripts/install-cli.sh"
"$HOME/.local/bin/dotfiles" setup "${setup_args[@]}"
echo 'Desktop setup completed. Keep a working TTY; see docs/recovery.md before opting into dotfiles setup-login.'
