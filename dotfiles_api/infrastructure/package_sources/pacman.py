import shutil
from dotfiles_api.domain.contracts.package_source import PackageSource
from dotfiles_api.context.execution import ExecutionContext

class PacmanSource(PackageSource):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def is_available(self) -> bool:
        return shutil.which("pacman") is not None

    def install(self, packages: list[str]) -> None:
        if not packages:
            return
        args = ["sudo", "pacman", "-S", "--needed", "--noconfirm"] + packages
        self._exec.execute(args)
