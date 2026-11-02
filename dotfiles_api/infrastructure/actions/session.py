from dotfiles_api.domain.contracts.action import Action


class SessionAction(Action):
    def __init__(self, session):
        self.session = session

    def execute(self, args):
        if args:
            raise ValueError("Session action takes no arguments")
        self.session.start()
