#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
setup_args=()
dry_run=false
for argument in "$@"; do
    case "$argument" in
        --dry-run) dry_run=true ;;
        --github|--ssh-server) setup_args+=("$argument") ;;
        -h|--help)
            echo 'Usage: bash scripts/bootstrap.sh [--dry-run] [--github] [--ssh-server]'
            echo 'Run interactively as a normal Arch user. Login setup is a separate dotfiles setup-login command.'
            exit 0 ;;
        *) printf 'Unknown option: %s\n' "$argument" >&2; exit 2 ;;
    esac
done

if "$dry_run"; then
    echo 'PLAN: back up pacman.conf; enable multilib; full system upgrade; install bootstrap packages'
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

# Preserve the previous package configuration before the first system change.
sudo cp -a --backup=numbered -- /etc/pacman.conf /etc/pacman.conf.shade-raid-backup
sudo sed -i '/^#\[multilib\]/s/^#//' /etc/pacman.conf
sudo sed -i '/^\[multilib\]/{n;s/^#//}' /etc/pacman.conf
sudo sed -i 's/^#Color$/Color/' /etc/pacman.conf
sudo sed -i 's/^#ParallelDownloads = 5$/ParallelDownloads = 5/' /etc/pacman.conf
sudo pacman -Syu --noconfirm
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
