# Fish Config Setup

## Changes to .config/fish/config.fish

### Auto-start Hyprland on TTY1
```fish
if status is-login
    if test -z "$DISPLAY" && test "$XDG_VTNR" = 1
        exec start-hyprland
    end
end
```

### SSH Agent Auto-start
```fish
if test -z "$SSH_AUTH_SOCK"
    eval (ssh-agent -c) 2>/dev/null
    ssh-add ~/.ssh/github-ssh
end
```

### Aliases
```fish
# Dotfiles management
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

# Theme & Config Reload
alias theme='~/.config/themes/apply.sh'
alias reload-waybar='pkill waybar; hyprctl dispatch exec waybar'
alias reload-swaync='pkill swaync; hyprctl dispatch exec swaync'
alias reload-walker='pkill walker; hyprctl dispatch exec "walker --gapplication-service"'
alias reload-hyprsunset='pkill hyprsunset; hyprctl dispatch exec hyprsunset'
alias reload-theme='~/.config/themes/apply.sh shade-raid'
alias reload-hyprland='hyprctl reload'

# Modern CLI Replacements
alias ll='eza -la --icons --git'
alias la='eza -a --icons'
alias ls='eza --icons'
alias cat='bat'
alias g='git'

# Tools
zoxide init fish | source
starship init fish | source
set fzf_fd_opts --hidden

# Hermes Agent — ensure ~/.local/bin is on PATH
fish_add_path "$HOME/.local/bin"
```

**Related Files:**
- .config/fish/config.fish - Main fish shell configuration
