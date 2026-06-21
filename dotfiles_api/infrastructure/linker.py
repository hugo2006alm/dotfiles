from pathlib import Path
from dotfiles_api.domain.contracts.linker import Linker
from dotfiles_api.context.execution import ExecutionContext

class StowLinker(Linker):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def link(self, source_dir: Path, target_dir: Path) -> None:
        args = ["stow", "-d", str(source_dir), "-t", str(target_dir), "."]
        self._exec.execute(args)
