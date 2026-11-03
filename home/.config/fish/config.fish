# ── Shell Greeting ────────────────────────────────────
set -g fish_greeting

# ── Auto-start Hyprland on TTY1 ───────────────────────
if status is-login
    if test -z "$DISPLAY" && test "$XDG_VTNR" = 1
        exec start-hyprland
    end
end

# ── SSH Agent ─────────────────────────────────────────
if test -z "$SSH_AUTH_SOCK"
    if test -n "$XDG_RUNTIME_DIR"
        set -gx SSH_AUTH_SOCK "$XDG_RUNTIME_DIR/shade-raid-ssh/agent.socket"
    end
end

# ── Aliases ───────────────────────────────────────────
function dotfiles_push
    set -l message $argv[1]
    if test -z "$message"
        echo "Usage: dotfiles_push \"commit message\""
        return 1
    end
    set -l old_pwd $PWD
    cd ~/dotfiles
    dotfiles link; or return
    git add -A
    git commit -m "$message"
    git push
    cd $old_pwd
end
alias theme='dotfiles configure --theme'
alias ll='eza -la --icons --git'
alias la='eza -a --icons'
alias ls='eza --icons'
alias cat='bat'
alias g='git'
alias reload-waybar='systemctl --user try-reload-or-restart shade-raid-waybar.service'
alias reload-swaync='swaync-client -R; swaync-client -rs'
alias reload-walker='systemctl --user try-restart shade-raid-walker.service'
alias reload-hyprsunset="pkill hyprsunset; hyprctl dispatch 'hl.dsp.exec_cmd(\"hyprsunset\")'"
alias reload-theme='dotfiles configure --theme shade-raid'
alias reload-hyprland='hyprctl reload'

# ── Zoxide init ───────────────────────────────────────
zoxide init fish | source

# ── Starship prompt ───────────────────────────────────
starship init fish | source

# ── Fzf Fish Config ───────────────────────────────────
set fzf_fd_opts --hidden

if status is-interactive
end

# Hermes Agent — ensure ~/.local/bin is on PATH
fish_add_path "$HOME/.local/bin"
