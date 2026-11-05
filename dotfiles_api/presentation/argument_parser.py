import argparse
import sys


class CommandParser(argparse.ArgumentParser):
    """Reserve CLI options before '--', preserving declared option values."""

    def parse_args(self, args=None, namespace=None):
        words = list(sys.argv[1:] if args is None else args)
        boundary = words.index("--") if "--" in words else len(words)
        children = next((action.choices for action in self._actions
                         if isinstance(action, argparse._SubParsersAction)), {})
        known = dict(self._option_string_actions)
        for child in children.values():
            known.update(child._option_string_actions)
        lifted, remaining, provided, values = [], [], set(), {}
        command, help_requested, index = None, False, 0
        while index < boundary:
            word = words[index]
            option, equals, inline = word.partition("=")
            action = known.get(option)
            if action is None:
                if command is None and word in children:
                    command = word
                remaining.append(word)
                index += 1
                continue
            tokens = [word]
            value = inline if equals else None
            if action.nargs != 0 and not equals and index + 1 < boundary:
                index += 1
                value = words[index]
                tokens.append(value)
            if option in {"--help", "-h"}:
                help_requested = True
            elif option in self._option_string_actions:
                provided.add(option)
                if action.nargs != 0 and value is not None:
                    if action.dest in values and values[action.dest] != value:
                        self.error(f"conflicting values for {option}; specify one value")
                    values[action.dest] = value
                lifted.extend(tokens)
            else:
                remaining.extend(tokens)
            index += 1
        if help_requested:
            children.get(command, self).print_help()
            self.exit()
        parsed = super().parse_args(lifted + remaining + words[boundary:], namespace)
        child = children.get(getattr(parsed, "command", None))
        global_flags = {"--dry-run", "--verbose", "-v"}
        for option in sorted(provided - global_flags):
            if child is not None and option not in child._option_string_actions:
                self.error(f"{option} is not valid for {parsed.command}")
        return parsed
