import errno
import hashlib
import json
import os
import time
import uuid
from pathlib import Path

from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.file_writer import SystemFileWriter


class ConfigTransaction:
    """Stage one batch, then replace files individually with a recovery journal."""

    def __init__(self, env, store, writer, dry_run: bool = False) -> None:
        self._env, self._store, self._writer = env, store, writer
        self._dry_run = dry_run
        self.theme_name = ""
        self.generators = []
        self._pending = {}
        self.last_journal = None

    @property
    def env(self):
        return self._env

    def __enter__(self):
        self._pending.clear()
        self.last_journal = None
        return self

    def write_artifact(self, artifact: GeneratedArtifact) -> None:
        path = self._store.resolve_path(artifact.artifact_id, theme_name=self.theme_name)
        self._env.validate_output_path(path)
        if self._dry_run:
            print(f"[DRY-RUN] Would write file {path}")
            return
        if path in self._pending:
            raise ValueError(f"Duplicate transaction destination: {path}")
        if path.is_file() and not path.is_symlink() and path.read_bytes() == artifact.content.encode("utf-8"):
            return
        self._pending[path] = artifact

    def _save_manifest(self, journal, manifest):
        SystemFileWriter().write(journal / "manifest.json", json.dumps(manifest, indent=2))

    def _commit(self):
        if not self._pending:
            return
        journal = self._env.state_dir / "transactions" / uuid.uuid4().hex
        self._env.validate_output_path(journal / "manifest.json")
        records, parents = [], set()
        for path, artifact in self._pending.items():
            self._env.validate_output_path(path)
            parent = path.parent
            while not parent.exists():
                parents.add(str(parent))
                parent = parent.parent
            if path.exists() and not path.is_file():
                raise ValueError(f"Generated destination is not a file: {path}")
            exists = path.exists() or path.is_symlink()
            info = path.lstat() if exists else None
            records.append({"path": str(path.absolute()), "artifact_id": artifact.artifact_id,
                            "exists": exists, "mode": info.st_mode & 0o777 if info else None,
                            "mtime_ns": info.st_mtime_ns if info else None,
                            "atime_ns": info.st_atime_ns if info else None,
                            "link": os.readlink(path) if path.is_symlink() else None,
                            "backup": str(len(records)),
                            "after_digest": hashlib.sha256(artifact.content.encode("utf-8")).hexdigest()})
        (journal / "backups").mkdir(parents=True, mode=0o700)
        (journal / "staging").mkdir(mode=0o700)
        for record, (path, artifact) in zip(records, self._pending.items()):
            if record["exists"] and record["link"] is None:
                backup = journal / "backups" / record["backup"]
                SystemFileWriter().write_bytes(backup, path.read_bytes())
            SystemFileWriter().write(journal / "staging" / record["backup"], artifact.content)
        manifest = {"version": 1, "created_ns": time.time_ns(), "theme": self.theme_name, "status": "prepared",
                    "generators": self.generators, "files": records, "parents": sorted(parents)}
        self._save_manifest(journal, manifest)
        self.last_journal = journal
        try:
            for path, artifact in self._pending.items():
                self._writer.write(path, artifact.content)
            manifest["status"] = "committed"
            self._save_manifest(journal, manifest)
        except BaseException as original:
            try:
                self._restore(journal, manifest)
                manifest["status"] = "rolled_back"
                self._save_manifest(journal, manifest)
            except BaseException as recovery:
                raise RuntimeError(f"Application failed; recovery incomplete. Journal {journal}: {recovery}") from original
            raise
        print(f"Theme recovery journal: {journal}")

    def _validated_records(self, journal, manifest):
        if manifest.get("version", 0) not in (0, 1):
            raise ValueError(f"Unsupported recovery journal version: {journal}")
        records = manifest["files"]
        for index, record in enumerate(records):
            expected = self._store.resolve_path(record["artifact_id"], theme_name=manifest["theme"]).absolute()
            if Path(record["path"]) != expected or record["backup"] != str(index):
                raise ValueError(f"Invalid recovery manifest: {journal}")
            self._env.validate_output_path(expected)
            backup = journal / "backups" / str(index)
            if record["exists"] and record["link"] is None and (backup.is_symlink() or not backup.is_file()):
                raise ValueError(f"Missing or unsafe recovery backup: {backup}")
        return records

    def _restore(self, journal, manifest):
        records = self._validated_records(journal, manifest)
        failures = []
        for record in reversed(records):
            path = Path(record["path"])
            try:
                record["recovery"] = "restoring"
                self._save_manifest(journal, manifest)
                if not record["exists"]:
                    path.unlink(missing_ok=True)
                elif record["link"] is not None:
                    temporary = path.parent / (".shade-raid-restore-" + uuid.uuid4().hex)
                    try:
                        temporary.symlink_to(record["link"])
                        os.replace(temporary, path)
                    finally:
                        temporary.unlink(missing_ok=True)
                    os.utime(path, ns=(record["atime_ns"], record["mtime_ns"]), follow_symlinks=False)
                else:
                    content = (journal / "backups" / record["backup"]).read_bytes()
                    SystemFileWriter().write_bytes(path, content)
                    path.chmod(record["mode"])
                    os.utime(path, ns=(record["atime_ns"], record["mtime_ns"]))
                record["recovery"] = "restored"
                self._save_manifest(journal, manifest)
            except OSError as error:
                failures.append(f"{path}: {error}")
        for value in sorted(manifest["parents"], key=lambda text: len(Path(text).parts), reverse=True):
            path = Path(value)
            self._env.validate_output_path(path)
            try:
                path.rmdir()
            except OSError as error:
                if error.errno not in {errno.ENOENT, errno.ENOTEMPTY}:
                    failures.append(f"{path}: {error}")
        if failures:
            raise RuntimeError("; ".join(failures))

    def rollback_latest(self, dry_run: bool = False):
        candidates = []
        for path in (self._env.state_dir / "transactions").glob("*/manifest.json"):
            if path.is_symlink():
                raise ValueError(f"Unsafe recovery manifest: {path}")
            manifest = json.loads(path.read_text())
            if manifest["status"] in {"committed", "prepared", "rolling_back"}:
                candidates.append((manifest["created_ns"], path.parent, manifest))
        if not candidates:
            raise ValueError("No recoverable theme transaction found.")
        _, journal, manifest = max(candidates, key=lambda item: item[0])
        for record in self._validated_records(journal, manifest):
            path = Path(record["path"])
            if record["artifact_id"] == "theme-preview":
                continue
            may_be_original = manifest["status"] == "prepared" or (manifest["status"] == "rolling_back" and record.get("recovery") in {"restoring", "restored"})
            if may_be_original and path.is_symlink() and os.readlink(path) == record["link"]:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            expected = {record["after_digest"]}
            if may_be_original:
                backup = journal / "backups" / record["backup"]
                if backup.is_file():
                    expected.add(hashlib.sha256(backup.read_bytes()).hexdigest())
                elif not record["exists"]:
                    expected.add(None)
            if path.is_symlink() or digest not in expected:
                raise RuntimeError(f"Generated destination changed since application: {path}")
        if dry_run:
            print(f"[DRY-RUN] Would restore {len(manifest['files'])} files from {journal}")
        else:
            manifest["status"] = "rolling_back"
            self._save_manifest(journal, manifest)
            self._restore(journal, manifest)
            manifest["status"] = "rolled_back"
            self._save_manifest(journal, manifest)
            print(f"Restored theme snapshot {journal.name}")
        return frozenset(manifest["generators"])

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self._commit()
        self._pending.clear()
        return False
