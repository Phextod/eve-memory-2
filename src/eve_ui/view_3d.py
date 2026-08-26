from typing import TYPE_CHECKING

from src.utils import utils
from src.utils.bubbling_query import BubblingQuery

if TYPE_CHECKING:
    # Only imported during static type checking, ignored at runtime
    from src.eve_ui.eve_ui import EveUI


class View3d:
    def __init__(self, eve_ui: 'EveUI', refresh_on_init=False):
        self.eve_ui: EveUI = eve_ui
        self.main_overlay_query = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            node_type="Toggled3DViewWarning",
            refresh_on_init=refresh_on_init
        )

    def is_3d_view_enabled(self):
        if self.main_overlay_query.run():
            return False
        return True

    @staticmethod
    def toggle_3d_view():
        utils.hold_and_release_keys(['ctrl', 'shift', 'f9'])
