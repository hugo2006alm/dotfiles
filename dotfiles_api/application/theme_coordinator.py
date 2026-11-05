from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.application.planner import ThemePlanner
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.application.preview_transaction import restore_preview, preview_projection
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.runtime_lock import RuntimeLock


class ThemeCoordinator:
    def __init__(self, env: EnvironmentContext, planner: ThemePlanner, transaction: ConfigTransaction) -> None:
        self.env, self.planner, self.transaction = env, planner, transaction

    def apply(self, tokens, theme_name: str, dry_run: bool = False):
        # Fail rendering/validation before creating locks or touching state.
        plan = self.planner.build(tokens, theme_name)
        if dry_run:
            plan.describe()
            print("No changes applied.")
            return plan
        with RuntimeLock(self.env.lock_dir / "configure.lock"):
            if restore_preview(self.env):
                plan = self.planner.build(tokens, theme_name)
            plan.describe()
            for item in plan.artifacts:
                current = item.path.read_bytes() if item.path.exists() else None
                link = str(item.path.readlink()) if item.path.is_symlink() else None
                if current != item.original or link != item.original_link:
                    raise RuntimeError(f"Generated destination changed after planning: {item.path}")
            self.transaction.theme_name = theme_name
            self.transaction.generators = sorted(plan.changed_generators)
            with self.transaction as transaction:
                for item in plan.artifacts:
                    if item.changed:
                        transaction.write_artifact(item.artifact)
                transaction.write_artifact(GeneratedArtifact("theme-preview", theme_name))
                transaction.write_artifact(GeneratedArtifact("active-theme", theme_name + "\n"))
        print(f"Applied theme {theme_name}.")
        return plan

    def rollback(self, dry_run: bool = False):
        if dry_run:
            return self.transaction.rollback_latest(dry_run=True, projected=preview_projection(self.env))
        with RuntimeLock(self.env.lock_dir / "configure.lock"):
            restore_preview(self.env)
            return self.transaction.rollback_latest()
