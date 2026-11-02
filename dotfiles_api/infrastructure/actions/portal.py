from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.application.services.wayland_session import WaylandSessionService


class PortalAction(Action):
    def __init__(self, exec_ctx, session=None):
        self.session = session or WaylandSessionService(exec_ctx)

    def execute(self, args):
        if args:
            raise ValueError("Portal action takes no arguments")
        self.session.ensure_portals()
