from pathlib import Path
from dotfiles_api.domain.contracts.linker import Linker
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.infrastructure.home_migration import HomeMigration

class StowLinker(Linker):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def link(self, source_dir: Path, target_dir: Path) -> None:
        args = ["stow", "--no-folding", "-d", str(source_dir), "-t", str(target_dir), "home"]
        migration = HomeMigration(source_dir, target_dir)
        if self._exec.dry_run:
            print(f"[DRY-RUN] Would migrate {len(migration.links)} legacy links; personal-file conflicts are preserved.")
            self._exec.execute(args, step="link:stow")
            return
        with migration:
            self._exec.execute(args, step="link:stow")
