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
            self.execution.execute(["walker", "--provider", "clipboard"], step="clipboard:history")
            return
        content = self.execution.execute(["wl-paste", "--no-newline"], step="clipboard:read").stdout
        path = self.env.runtime_dir / f"clipboard-{uuid4().hex}.txt"
        self.env.validate_output_path(path)
        SystemFileWriter().write(path, content)
        script = 'trap \'rm -f -- "$1"\' EXIT; nvim -- "$1" && wl-copy < "$1"'
        try:
            self.execution.execute(["ghostty", "-e", "sh", "-c", script, "shade-raid-clipboard", str(path)],
                                   step="clipboard:edit")
        except BaseException:
            path.unlink(missing_ok=True)
            raise
