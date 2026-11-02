import re
import shlex


def redacted_diagnostics(args: list[str], diagnostic: str = "") -> tuple[str, str]:
    """Redact credential arguments, URL authentication and common token formats."""
    sensitive = {"--password", "--token", "--api-key", "--secret", "--client-secret"}
    safe = list(args)
    secrets = []
    for index, argument in enumerate(args):
        if index and args[index - 1].lower() in sensitive:
            secrets.append(argument)
            safe[index] = "[REDACTED]"
        elif "=" in argument and argument.split("=", 1)[0].lower() in sensitive:
            key, value = argument.split("=", 1)
            secrets.append(value)
            safe[index] = key + "=[REDACTED]"

    def redact(value: str) -> str:
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        value = re.sub(r"(?i)(https?://)[^/\s@]+@", r"\1[REDACTED]@", value)
        value = re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)", "[REDACTED]", value)
        value = re.sub(r"(?i)(--(?:password|token|api-key|secret|client-secret)(?:=|\s+))[^\s'\"]+", r"\1[REDACTED]", value)
        return value

    return redact(shlex.join(safe)), redact(diagnostic)[:2000]
