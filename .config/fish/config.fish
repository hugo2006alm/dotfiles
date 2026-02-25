# ── Auto-start Hyprland on TTY1 ───────────────────────
if status is-login
    if test -z "$DISPLAY" && test "$XDG_VTNR" = 1
        exec start-hyprland
    end
end

# ── SSH Agent ─────────────────────────────────────────
if test -z "$SSH_AUTH_SOCK"
    eval (ssh-agent -c) 2>/dev/null
    ssh-add ~/.ssh/github-ssh
end

# ── Aliases ───────────────────────────────────────────
alias dots='git --git-dir=$HOME/.dotfiles --work-tree=$HOME'
alias ll='eza -la --icons --git'
alias la='eza -a --icons'
alias ls='eza --icons'
alias cat='bat'
alias g='git'

# ── Zoxide init ───────────────────────────────────────
zoxide init fish | source

# ── Starship prompt ───────────────────────────────────
starship init fish | source

if status is-interactive
end
