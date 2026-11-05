import os
import shutil
import tempfile
from pathlib import Path
from dotfiles_api.domain.contracts.linker import Linker
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.infrastructure.home_migration import HomeMigration

class StowLinker(Linker):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def preflight(self, source_dir: Path, target_dir: Path) -> None:
        HomeMigration(source_dir, target_dir).preflight()

    def link(self, source_dir: Path, target_dir: Path) -> None:
        args = ["stow", "--no-folding", "-d", str(source_dir), "-t", str(target_dir), "home"]
        migration = HomeMigration(source_dir, target_dir)
        if self._exec.dry_run:
            print(f"[DRY-RUN] Would migrate {len(migration.links)} legacy links; personal-file conflicts are preserved.")
            self._exec.execute(args, step="link:stow")
            return
        with migration:
            self._exec.execute(args, step="link:stow")
            self._install_seeds(source_dir, target_dir)

    def _install_seeds(self, source: Path, target: Path) -> None:
        seeds = source / "seeds"
        if not seeds.is_dir():
            return
        for item in sorted(seeds.rglob("*")):
            if not item.is_file() or item.is_symlink():
                continue
            destination = target / item.relative_to(seeds)
            if destination.exists() or destination.is_symlink():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.parent.resolve().is_relative_to(source.resolve()):
                raise ValueError(f"Unsafe seed destination: {destination}")
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".shade-raid-seed-", delete=False) as out:
                    temporary = Path(out.name)
                    with item.open("rb") as source_file:
                        shutil.copyfileobj(source_file, out)
                try:
                    os.link(temporary, destination, follow_symlinks=False)
                except FileExistsError:
                    pass
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
