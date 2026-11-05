import fcntl
import hashlib
import json
import os
import pwd
import re
import signal
import stat
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from dotfiles_api.infrastructure.login_preflight import LoginPreflight


class LoginInstallation:
    """Fixed root paths, private backups, atomic replacement and compensating recovery."""

    NAMES = ('hyprland-greet.conf', 'regreet.toml', 'regreet.css', 'config.toml', 'regreet-background.jpg')
    SUDOERS = ('shade-raid', 'plymouth_sync', 'regreet-theme')

    def __init__(self, root=Path('/'), owner=0, group=0, after_effect=None, policy_check=None):
        self.root, self.owner, self.group = Path(root), owner, group
        self.after_effect, self.steps = after_effect, 0
        self.policy_check = policy_check or self.check_policy
        self._locked = False

    @staticmethod
    def check_policy():
        result = subprocess.run(['/usr/bin/visudo', '-c'], check=False)
        if result.returncode:
            raise ValueError('Sudoers policy validation failed; inspect it from a recovery TTY')

    @staticmethod
    def legacy_rule(user, home):
        return (f'{user} ALL=(ALL) NOPASSWD: /usr/bin/cp {home}/.config/greetd/regreet.css /etc/greetd/regreet.css\n'
                f'{user} ALL=(ALL) NOPASSWD: /usr/bin/cp {home}/dotfiles/.config/greetd/hyprland-greet.conf /etc/greetd/hyprland-greet.conf\n')

    def directories(self, path):
        if not path.is_relative_to(self.root):
            raise ValueError('Login path escaped the fixed system root')
        items = [self.root]
        for part in path.relative_to(self.root).parts:
            items.append(items[-1] / part)
        for item in items:
            if not item.exists() and not item.is_symlink():
                continue
            info = item.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != self.owner or info.st_mode & 0o022:
                raise ValueError(f'Unsafe login directory owner, mode or link: {item}')

    def directory(self, path, mode=0o700):
        self.directories(path)
        if path.exists() and mode == 0o700 and path.stat().st_mode & 0o077:
            raise ValueError(f'Private login directory has broad permissions: {path}')
        if not path.exists():
            path.mkdir(mode=mode)
            os.chown(path, self.owner, self.group)

    def targets(self):
        return {**{f'greetd/{name}': self.root / 'etc/greetd' / name for name in self.NAMES},
                **{f'sudoers/{name}': self.root / 'etc/sudoers.d' / name for name in self.SUDOERS}}

    def preflight(self, payload):
        if (payload.get('version') != 1 or not isinstance(payload.get('permissions_only'), bool)
                or not isinstance(payload.get('files'), dict)
                or not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_-]*', payload.get('user', ''))
                or not isinstance(payload.get('home'), str) or not Path(payload['home']).is_absolute()
                or any(char in payload['home'] for char in '\n\r\x00')):
            raise ValueError('Invalid login installation request')
        files = payload['files']
        if payload['permissions_only']:
            if files:
                raise ValueError('Permission remediation cannot replace configuration inputs')
        elif set(files) != {'hyprland-greet.conf', 'regreet.toml', 'regreet.css', 'config.toml'}:
            raise ValueError('Invalid login snapshot names')
        if not all(isinstance(value, str) for value in files.values()):
            raise ValueError('Login snapshot values must be text')
        if payload.get('backup_id') and not re.fullmatch('[0-9a-f]{32}', payload['backup_id']):
            raise ValueError('Invalid login backup ID')
        if sum(len(value.encode()) for value in files.values()) > LoginPreflight.LIMIT:
            raise ValueError('Login snapshot exceeds safe size')
        LoginPreflight.validate_files(files)
        for path in (self.root / 'etc/greetd', self.root / 'etc/sudoers.d', self.root / 'var/backups',
                     self.root / 'var/backups/shade-raid', self.root / 'run'):
            self.directories(path)
        for path in self.targets().values():
            if path.exists() or path.is_symlink():
                if not stat.S_ISREG(path.lstat().st_mode):
                    raise ValueError(f'Expected a regular destination, not a link/device: {path}')
                if path.lstat().st_nlink != 1:
                    raise ValueError(f'Refusing hard-linked login destination: {path}')
        if not payload['permissions_only']:
            LoginPreflight.check_display_manager(self.root)

    def write(self, path, data, mode=0o600, owner=None, group=None):
        fd, staged = tempfile.mkstemp(prefix='.shade-raid-', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fchown(stream.fileno(), self.owner if owner is None else owner,
                          self.group if group is None else group)
                os.fchmod(stream.fileno(), mode)
                os.fsync(stream.fileno())
            os.replace(staged, path)
        finally:
            Path(staged).unlink(missing_ok=True)

    def save(self, backup, manifest):
        self.write(backup / 'manifest.json', (json.dumps(manifest, indent=2) + '\n').encode())

    def effect(self):
        self.steps += 1
        if self.after_effect:
            self.after_effect(self.steps)

    def restore(self, backup):
        """Restore the fixed snapshot; repeat safely after a failed recovery."""
        if (backup.parent != self.root / 'var/backups/shade-raid' or
                not re.fullmatch(r'login-[0-9a-f]{32}', backup.name)):
            raise ValueError('Recovery must use a fixed login backup path')
        if not self._locked:
            return self.locked(lambda: self.restore(backup))
        self.directories(backup)
        manifest = json.loads(LoginPreflight.regular_bytes(backup / 'manifest.json'))
        if manifest.get('version') != 1 or not isinstance(manifest.get('originals'), dict):
            raise ValueError('Unsupported login recovery manifest')
        targets = self.targets()
        if set(manifest['originals']) != set(targets):
            raise ValueError('Invalid login recovery paths')
        manifest['state'] = 'recovering'
        self.save(backup, manifest)
        for key, path in targets.items():
            original = manifest['originals'][key]
            if not original['changed']:
                continue
            self.directories(path.parent)
            if path.exists() or path.is_symlink():
                if not stat.S_ISREG(path.lstat().st_mode):
                    raise ValueError(f'Recovery destination changed type: {path}')
            if original['exists']:
                data = LoginPreflight.regular_bytes(backup / key)
                if hashlib.sha256(data).hexdigest() != original['sha256']:
                    raise ValueError(f'Corrupt login backup: {backup / key}')
                self.write(path, data, original['mode'], original['uid'], original['gid'])
            else:
                path.unlink(missing_ok=True)
        directory = self.root / 'etc/greetd'
        if manifest['directory'] is None:
            if directory.exists(): directory.rmdir()
        else:
            mode, uid, gid = manifest['directory']
            os.chown(directory, uid, gid)
            directory.chmod(mode)
        manifest['state'] = 'restored'
        self.save(backup, manifest)

    def locked(self, operation):
        lock_dir = self.root / 'run/shade-raid-login'
        self.directory(lock_dir)
        fd = os.open(lock_dir / 'install.lock', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != self.owner or info.st_nlink != 1:
                raise ValueError('Unsafe root login lock')
            os.fchmod(fd, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX)
            self._locked = True
            return operation()
        finally:
            self._locked = False
            os.close(fd)

    def apply(self, payload):
        self.steps = 0
        self.preflight(payload)
        def run():
            self.preflight(payload)
            return self.apply_locked(payload)
        return self.locked(run)

    def apply_locked(self, payload):
        directory = self.root / 'etc/greetd'
        directory_info = directory.stat() if directory.exists() else None
        originals, current = {}, {}
        for key, path in self.targets().items():
            exists = path.exists()
            record = {'exists': exists, 'changed': False}
            if exists:
                info = path.stat()
                current[key] = LoginPreflight.regular_bytes(path)
                record.update(mode=stat.S_IMODE(info.st_mode), uid=info.st_uid, gid=info.st_gid,
                              sha256=hashlib.sha256(current[key]).hexdigest())
            originals[key] = record
        if payload['permissions_only']:
            LoginPreflight.validate_files({key.split('/')[1]: data.decode('utf-8')
                                          for key, data in current.items()
                                          if key.startswith('greetd/') and not key.endswith('.jpg')})
        self.policy_check()
        self.directory(self.root / 'var/backups', 0o755)
        backup_root = self.root / 'var/backups/shade-raid'
        self.directory(backup_root)
        backup = backup_root / ('login-' + (payload.get('backup_id') or uuid.uuid4().hex))
        backup.mkdir(mode=0o700)
        os.chown(backup, self.owner, self.group)
        self.directory(backup / 'greetd')
        self.directory(backup / 'sudoers')
        for key, data in current.items():
            self.write(backup / key, data)
        manifest = {'version': 1, 'state': 'prepared', 'originals': originals,
                    'directory': [stat.S_IMODE(directory_info.st_mode), directory_info.st_uid,
                                  directory_info.st_gid] if directory_info else None}
        self.save(backup, manifest)
        print(f'Login backup: {backup}', flush=True)
        try:
            self.directory(directory, 0o755)
            directory.chmod(0o755)
            os.chown(directory, self.owner, self.group)
            self.effect()
            for key, path in self.targets().items():
                name = path.name
                if (path.exists() != originals[key]['exists'] or
                        (key in current and LoginPreflight.regular_bytes(path) != current[key])):
                    raise ValueError(f'Login destination changed after snapshot: {path}')
                if key.startswith('greetd/'):
                    if name in payload['files']:
                        data = payload['files'][name].encode()
                    elif key in current:
                        data = current[key]
                    else:
                        continue
                    originals[key]['changed'] = True
                    self.save(backup, manifest)
                    self.write(path, data, 0o644)
                    self.effect()
                elif key in current:
                    expected = self.legacy_rule(payload['user'], payload['home']).encode()
                    if name == 'shade-raid' and current[key] == expected and originals[key]['uid'] == self.owner:
                        originals[key]['changed'] = True
                        self.save(backup, manifest)
                        path.unlink()
                        self.effect()
                    else:
                        print(f'Preserved custom/unrecognized sudoers: {path}; inspect it manually')
            self.policy_check()
            manifest['state'] = 'applied'
            self.save(backup, manifest)
            self.effect()
        except BaseException:
            try:
                self.restore(backup)
            except BaseException as recovery_error:
                manifest['state'] = 'recovery-required'
                self.save(backup, manifest)
                raise RuntimeError(f'Login recovery incomplete; retain backup {backup}: {recovery_error}') from recovery_error
            raise
        print('Login files secured. Display-manager enablement is unchanged; verify from a recovery TTY.')
        return backup


def _interrupt_login(number, frame):
    raise InterruptedError('Login installation interrupted')


def _privileged_main():
    if os.geteuid() != 0:
        raise SystemExit('The login helper requires an explicitly authorized root invocation')
    payload = json.loads(sys.argv[1])
    account = pwd.getpwnam(payload.get('user', ''))
    if (str(account.pw_uid) != os.environ.get('SUDO_UID')
            or account.pw_dir != payload.get('home')):
        raise SystemExit('Login request does not match the invoking user/HOME')
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _interrupt_login)
    LoginInstallation().apply(payload)


if __name__ == '__main__':
    _privileged_main()
