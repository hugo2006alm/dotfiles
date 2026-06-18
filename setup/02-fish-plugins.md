# Fish Plugins Setup

## Changes to `.config/fish/fish_plugins`

### Plugins (managed by Fisher)

The following plugins are installed and managed via Fisher:

| Plugin | Author | Purpose |
|--------|--------|---------|
| `fisher` | jorgebucaran | Plugin manager for Fish |
| `fzf.fish` | patrickf1 | FZF integration for Fish |
| `autopair.fish` | jorgebucaran | Auto-pair brackets, quotes, etc. |
| `nvm.fish` | jorgebucaran | Node Version Manager integration |
| `sdkman-for-fish` | reitzig | SDKMAN integration for Java/JVM tools |

### Installation

After updating `fish_plugins`, run:
```bash
fisher update
```

### File: `.config/fish/fish_plugins`
```
jorgebucaran/fisher
patrickf1/fzf.fish
jorgebucaran/autopair.fish
jorgebucaran/nvm.fish
reitzig/sdkman-for-fish
```

**Related Files:**
- `.config/fish/fish_plugins` - Plugin list for Fisher
- `.config/fish/config.fish` - Main fish shell configuration
