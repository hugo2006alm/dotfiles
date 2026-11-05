import shutil
from uuid import uuid4
from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.infrastructure.file_writer import SystemFileWriter


class ClipboardAction(Action):
    def __init__(self, execution, env, edit=False):
        self.execution, self.env, self.edit = execution, env, edit

    def execute(self, args):
        if args:
            raise ValueError("Clipboard actions take no arguments")
        if self.execution.dry_run:
            print("[DRY-RUN] Would open clipboard history/editor")
            return
        tools = ("wl-paste", "wl-copy", "ghostty", "nvim") if self.edit else ("walker",)
        missing = [tool for tool in tools if not shutil.which(tool)]
        if missing:
            raise RuntimeError("Clipboard requires: " + ", ".join(missing))
        if not self.edit:
            self.execution.spawn(["walker", "--provider", "clipboard"], step="clipboard:history", sensitive=True)
            return
        mime_types = self.execution.execute(["wl-paste", "--list-types"], step="clipboard:types", sensitive=True).stdout.splitlines()
        plain_text = next((mime.strip() for mime in mime_types if mime.strip().lower().split(";", 1)[0] == "text/plain"), None)
        if not plain_text:
            raise ValueError("Clipboard does not offer plain text")
        content = self.execution.execute(["wl-paste", "--type", plain_text, "--no-newline"],
                                         step="clipboard:read", sensitive=True).stdout
        if not content:
            raise ValueError("Clipboard is empty")
        path = self.env.runtime_dir / f"clipboard-{uuid4().hex}.txt"
        self.env.validate_output_path(path)
        SystemFileWriter().write(path, content)
        script = 'trap \'rm -f -- "$1"\' EXIT; nvim -- "$1" && wl-copy < "$1"'
        try:
            self.execution.execute(["ghostty", "-e", "sh", "-c", script, "shade-raid-clipboard", str(path)],
                                   step="clipboard:edit", sensitive=True)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
