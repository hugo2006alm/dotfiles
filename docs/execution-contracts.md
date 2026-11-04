# Execution and failure contracts

Use `ExecutionContext.execute` for short commands with a checked exit status.
Required failures raise `CommandExecutionError`; optional failures are reported
and return their real result. Queries declare allowed absence exit codes.
`CommandResult.output_captured` distinguishes captured output from inherited
interactive terminal output. Interactive failures cannot promise captured stderr.
Privileged commands require an interactive terminal and are never spawned.

Use `ExecutionContext.spawn(args, step="launch:application")` for a long-lived
application. It returns a caller-owned process handle (`None` in dry-run), uses
no captured pipes or terminal input/output, and observes startup for at most 0.1s.
An immediate nonzero exit or failed spawn raises a safe error. A running child
gets a log record with PID and `returncode: null`, which means still running at
observation, not ready or successful for its lifetime. Keep the handle and use
poll/wait/terminate as appropriate for the consumer. Later application failures
need the consumer's lifecycle policy. Recorder readiness/finalization remains a
separate application-specific contract.

Launch arguments/diagnostics are private by default. For another private command,
such as clipboard editing, use `execute(..., sensitive=True)` (also supported by
optional/query). Browser, clipboard and shell commands are defensively private
even without the flag. URLs are removed in full, and URL-related stderr is
withheld because callback/path/fragment tokens can be echoed separately.
Authorization headers, credential flags and common tokens are redacted. Command
stdout is returned to the caller; do not print clipboard or private app output.

Command logging is a separate observation. A logging IO/validation failure emits
a fixed OBSERVABILITY warning while preserving the command result. Supply an
`output_guard` to reject log paths escaping managed locations or resolving into
the source repository; this logging guard runs inside the protected logger.
CLI/environment preflight still owns validation before operational effects.

Reloads run synchronously. Every selected reloader is attempted; required errors
are aggregated and raised after the attempts, so CLI refresh failures remain
visible. Explicit `optional_reloadables` are reported without making the whole
refresh fail. A busy refresh is a failure requiring retry, not queued success.
Theme commands observe reload completion rather than discarding a detached
reload child's exit status. Offline/pending-session refresh is a later consumer
policy, not proof that the desktop refreshed successfully.

Installation source preflight runs before installation groups. If a group fails,
`InstallationError.completed_groups` identifies group commands already completed
and `failed_source` identifies the interrupted group. The failed group may itself
have partial effects. Package changes are not rolled back; retry must inspect
actual inventory. This is separate from a complete desktop/setup result.

Browser/launcher consumers, checked screenshot-to-clipboard integration, recorder
readiness and clipboard MIME handling belong to their daily-desktop PR. These
contracts do not claim that those graphical integrations have been validated.
