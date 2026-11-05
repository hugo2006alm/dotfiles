from dotfiles_api.domain.contracts.reloadable import EventReloadable


class UserServiceReloadable(EventReloadable):
    def __init__(self, execution, application, unit):
        self.execution, self.application, self.unit = execution, application, unit

    def reload(self):
        self.execution.execute(["systemctl", "--user", "try-restart", self.unit], step=f"reload:{self.application}")

    def supports(self, generator_name):
        return generator_name == self.application
