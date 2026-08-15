from collections.abc import Callable


class OptionalPackageSelectionService:
    def __init__(
        self,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self._input = input_fn
        self._output = output_fn

    def select(self, options: list[dict[str, object]]) -> list[str]:
        selected: set[str] = set()

        while True:
            self._render(options, selected)
            answer = self._input(
                "Choose a number to toggle, [a]ll, [n]one, or [c]ontinue: "
            ).strip().lower()

            if answer in {"a", "all"}:
                selected.clear()
                for option in options:
                    self._enable(option, selected)
                continue

            if answer in {"n", "none"}:
                selected.clear()
                continue

            if answer in {"c", "continue", "done"}:
                ordered = self._ordered_selection(options, selected)
                self._output("")
                self._output("Selected packages:")
                if ordered:
                    for package in ordered:
                        self._output(f"  - {package}")
                else:
                    self._output("  (none)")

                confirm = self._input("Confirm this selection? [Y/n]: ").strip().lower()
                if confirm in {"", "y", "yes", "s", "sim"}:
                    return ordered
                continue

            try:
                index = int(answer) - 1
            except ValueError:
                self._output("Invalid choice.")
                continue

            if index < 0 or index >= len(options):
                self._output("Invalid choice.")
                continue

            option = options[index]
            package = str(option["package"])
            if package in selected:
                selected.remove(package)
            else:
                self._enable(option, selected)

    def _enable(self, option: dict[str, object], selected: set[str]) -> None:
        package = str(option["package"])
        for conflict in option.get("conflicts", []):
            selected.discard(str(conflict))
        selected.add(package)

    @staticmethod
    def _ordered_selection(options: list[dict[str, object]], selected: set[str]) -> list[str]:
        return [str(option["package"]) for option in options if str(option["package"]) in selected]

    def _render(self, options: list[dict[str, object]], selected: set[str]) -> None:
        self._output("")
        self._output("Optional packages")
        self._output("-----------------")

        current_category: str | None = None
        for index, option in enumerate(options, start=1):
            category = str(option.get("category", "Other"))
            if category != current_category:
                current_category = category
                self._output(f"\n{category}:")

            package = str(option["package"])
            label = str(option.get("label", package))
            source = str(option.get("source", "pacman"))
            marker = "x" if package in selected else " "
            self._output(f"  {index:>2}. [{marker}] {label} ({package}, {source})")

        self._output("")
        self._output("Tip: choose 'all' or 'none' first, then toggle individual entries.")
