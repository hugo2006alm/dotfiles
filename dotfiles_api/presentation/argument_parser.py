import argparse
import sys


class CommandParser(argparse.ArgumentParser):
    """Recognize global safety flags even after action arguments, before '--'."""

    def parse_args(self, args=None, namespace=None):
        words = list(sys.argv[1:] if args is None else args)
        boundary = words.index("--") if "--" in words else len(words)
        flags = {"--dry-run", "--verbose", "-v"}
        global_flags = [word for word in words[:boundary] if word in flags]
        remaining = [word for word in words[:boundary] if word not in flags] + words[boundary:]
        return super().parse_args(global_flags + remaining, namespace)
