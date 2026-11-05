# Home migration

`dotfiles link` examines legacy folded links before changing them. If old content overlaps a managed file but differs, the migration stops before unlinking anything. Inspect the reported path and save the preferred content outside the repository before resolving the conflict and retrying. The migration does not infer whether a difference is a customization.

Legacy links are backed up under `~/.shade-raid-backups/stow-*`. When a later migration step fails, the original links are restored and the unfolded contents are retained in `failed-contents` in the backup. Inspect both the original and retained data before removing a backup.

Mutable preferences are installed from `seeds/` as independent files only when absent. Existing personal files and existing legacy content are retained. The tracked seeds remain defaults, not live application state.

Directory modes are applied before contents are copied; file and directory timestamps are copied where possible. The migration uses Python `copy2`/`copystat`, which may copy platform-supported extended attributes on Linux, but does not promise ACL or all xattr preservation. Back up and restore ACLs or security labels separately when required. Relative symlinks are rewritten to preserve their absolute target.
