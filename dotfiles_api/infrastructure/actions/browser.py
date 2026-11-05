import shutil
from dotfiles_api.domain.contracts.action import Action


class BrowserAction(Action):
    def __init__(self, execution, chatgpt=False):
        self.execution, self.chatgpt = execution, chatgpt

    def execute(self, args):
        if self.chatgpt and args:
            raise ValueError("ChatGPT action takes no arguments")
        urls = ["https://chatgpt.com/"] if self.chatgpt else args
        # Direct browser invocation avoids recursion through our MIME wrapper.
        browser = next((name for name in ("zen-browser", "zen", "firefox", "chromium", "google-chrome", "brave")
                        if shutil.which(name)), None)
        if not browser:
            if self.execution.dry_run:
                print("[DRY-RUN] Would open an installed browser")
                return
            self.execution.optional(["notify-send", "Browser unavailable", "Install a browser or the daily profile"])
            raise RuntimeError("No supported browser installed; install the daily profile or Firefox/Chromium")
        self.execution.spawn([browser, *urls], step="launch:browser", sensitive=True)
