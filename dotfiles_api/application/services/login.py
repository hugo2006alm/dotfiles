import json
import subprocess
import sys
import uuid
from pathlib import Path

from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.infrastructure.login_installation import LoginInstallation
from dotfiles_api.infrastructure.login_lock import login_inputs_lock
from dotfiles_api.infrastructure.login_preflight import LoginPreflight


class LoginSetupService:
    """Explicit interactive login installation, separate from ordinary theme refresh."""

    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext, *, preflight=None, run=None, installer_preflight=None):
        self._exec, self._env = exec_ctx, env
        self._preflight = preflight or LoginPreflight(env)
        self._run = run or subprocess.run
        self._installer_preflight = installer_preflight or LoginInstallation(self._preflight.root).preflight

    def apply(self, permissions_only=False) -> Path | None:
        if not self._exec.dry_run and not sys.stdin.isatty():
            raise RuntimeError('Login changes require an interactive terminal; run this command yourself.')
        # Reject predictable input errors before creating even the unprivileged lock.
        payload = self._preflight.build(permissions_only=permissions_only)
        self._installer_preflight(payload)
        if self._exec.dry_run:
            operation = 'secure existing login permissions' if permissions_only else 'install validated login snapshot'
            print(f'[DRY-RUN] Would back up and {operation}; preserve custom sudoers and display-manager enablement.')
            return
        with login_inputs_lock(self._env.home_dir):
            payload = self._preflight.build(permissions_only=permissions_only)
            self._installer_preflight(payload)
            payload['backup_id'] = uuid.uuid4().hex
            # Pass immutable source text and JSON, never a user-writable helper or staging path to root.
            folder = Path(__file__).resolve().parents[2] / 'infrastructure'
            preflight_code = (folder / 'login_preflight.py').read_text(encoding='utf-8-sig')
            installer_code = (folder / 'login_installation.py').read_text(encoding='utf-8-sig')
            installer_code = installer_code.replace('from dotfiles_api.infrastructure.login_preflight import LoginPreflight\n', '')
            result = self._run(['sudo', '/usr/bin/python3', '-I', '-c', preflight_code + '\n' + installer_code,
                                 json.dumps(payload)])
            if result.returncode:
                raise RuntimeError(f'Login operation failed ({result.returncode}); inspect the printed backup/recovery status.')
        print('Keep a recovery TTY open. Review docs/login-recovery.md before manually enabling greetd.')
        return Path('/var/backups/shade-raid') / ('login-' + payload['backup_id'])
