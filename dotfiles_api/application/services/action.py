from dotfiles_api.domain.contracts.action import Action

class ActionService:
    def __init__(self) -> None:
        self._actions: dict[str, Action] = {}

    def register(self, name: str, action: Action) -> None:
        self._actions[name] = action

    def run_action(self, name: str, args: list[str]) -> None:
        if name not in self._actions:
            raise KeyError(f"Action '{name}' not registered.")
        self._actions[name].execute(args)
