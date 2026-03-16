# Fish Config Setup

## Changes to `.config/fish/config.fish`

### Added: `dots_commit_push` function

Adds a convenient function to commit and push dotfiles changes in one command:

```fish
function dots_commit_push
    set -l message $argv[1]
    if test -z "$message"
        echo "Usage: dots_commit_push \"commit message\""
        return 1
    end
    dots add -A
    dots commit -m "$message"
    dots push
end
```

**Usage:**
```bash
dots_commit_push "update fish config"
```

This function:
1. Stages all changes (`dots add -A`)
2. Creates a commit with the provided message
3. Pushes to remote repository

**Related Files:**
- `.config/fish/config.fish` - Main fish shell configuration
