from dotfiles_api.domain.contracts.reloadable import Reloadable
from dotfiles_api.application.services.wayland_session import WaylandSessionService


class XDGPortalReloadable(Reloadable):
    """Compatibility adapter; portal activation is independent of theme refresh."""

    def __init__(self, exec_ctx):
        self.session = WaylandSessionService(exec_ctx)

    def reload(self):
        self.session.ensure_portals()
