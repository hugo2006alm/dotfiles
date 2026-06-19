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
function dotfiles_push
    set -l message $argv[1]
    if test -z "$message"
        echo "Usage: dotfiles_push \"commit message\""
        return 1
    end
    set -l old_pwd $PWD
    cd ~/dotfiles
    stow . -t ~
    git add -A
    git commit -m "$message"
    git push
    cd $old_pwd
end
alias theme='~/.config/themes/apply.sh'
alias ll='eza -la --icons --git'
alias la='eza -a --icons'
alias ls='eza --icons'
alias cat='bat'
alias g='git'
alias reload-waybar='pkill waybar; hyprctl dispatch exec waybar'
alias reload-mako='pkill mako; hyprctl dispatch exec mako'
alias reload-walker='pkill walker; hyprctl dispatch exec "walker --gapplication-service"'
alias reload-hyprsunset='pkill hyprsunset; hyprctl dispatch exec hyprsunset'
alias reload-theme='~/.config/themes/apply.sh shade-raid'
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
