import hashlib
import json
from dotfiles_api.application.store import ArtifactStore
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.infrastructure.file_writer import SystemFileWriter


def preview_transaction(env):
    store = ArtifactStore({
        "swaync-config": env.home_dir / ".config/swaync/config.json",
        "swaync-style": env.home_dir / ".config/swaync/style.css",
        "theme-preview": env.preview_file,
    })
    return ConfigTransaction(env, store, SystemFileWriter(), journal_namespace="preview-transactions")


def restore_preview(env, dry_run=False):
    """Restore a preview overlay before any managed theme write or rollback.

    Caller must hold configure.lock. A prepared journal may represent an interrupted
    preview, so it is recovered before reading/writing the theme transaction.
    """
    tx = preview_transaction(env)
    manifests = (env.state_dir / "preview-transactions").glob("*/manifest.json")
    for path in manifests:
        if path.is_symlink():
            raise ValueError(f"Unsafe preview recovery manifest: {path}")
        manifest = json.loads(path.read_text())
        if manifest.get("status") in {"committed", "prepared", "rolling_back"}:
            tx.rollback_latest(dry_run=dry_run)
            return True
    return False


def preview_projection(env):
    """Validate preview recovery and project restored states without writing."""
    tx = preview_transaction(env)
    candidates = []
    for path in (env.state_dir / "preview-transactions").glob("*/manifest.json"):
        if path.is_symlink():
            raise ValueError(f"Unsafe preview recovery manifest: {path}")
        manifest = json.loads(path.read_text())
        if manifest.get("status") in {"committed", "prepared", "rolling_back"}:
            candidates.append((manifest["created_ns"], path.parent, manifest))
    if not candidates:
        return {}
    _, journal, manifest = max(candidates, key=lambda item: item[0])
    tx.rollback_latest(dry_run=True)
    result = {}
    for record in tx._validated_records(journal, manifest):
        link = record["link"]
        digest = None
        if record["exists"] and link is None:
            digest = hashlib.sha256((journal / "backups" / record["backup"]).read_bytes()).hexdigest()
        result[record["path"]] = (link is not None, link, digest)
    return result
