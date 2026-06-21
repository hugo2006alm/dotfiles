import shutil
from dotfiles_api.domain.contracts.package_source import PackageSource
from dotfiles_api.context.execution import ExecutionContext

class YaySource(PackageSource):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def is_available(self) -> bool:
        return shutil.which("yay") is not None

    def install(self, packages: list[str]) -> None:
        if not packages:
            return
        args = ["yay", "-S", "--needed", "--noconfirm"] + packages
        self._exec.execute(args)
