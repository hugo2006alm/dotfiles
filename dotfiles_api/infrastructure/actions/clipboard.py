import os
import shutil
from dotfiles_api.domain.contracts.action import Action


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
        # Keep clipboard text in anonymous memory. No on-disk temp, swap or backup.
        if not hasattr(os, "memfd_create"):
            raise RuntimeError("Clipboard editor requires Linux anonymous memory support")
        fd = os.memfd_create("shade-raid-clipboard", flags=os.MFD_CLOEXEC)
        try:
            os.fchmod(fd, 0o600)
            data = content.encode("utf-8")
            while data:
                count = os.write(fd, data)
                if count <= 0:
                    raise OSError("Unable to prepare clipboard buffer")
                data = data[count:]
            path = f"/proc/{os.getpid()}/fd/{fd}"
            script = ('nvim -u NONE -i NONE -n --noplugin --cmd "set noswapfile nobackup nowritebackup noundofile backupcopy=yes" '
                      '-- "$1" && wl-copy < "$1"')
            self.execution.execute(["ghostty", "-e", "sh", "-c", script, "shade-raid-clipboard", path],
                                   step="clipboard:edit", sensitive=True)
        finally:
            os.close(fd)
