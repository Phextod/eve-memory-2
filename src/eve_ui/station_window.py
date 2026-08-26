from typing import TYPE_CHECKING

from src.utils.bubbling_query import BubblingQuery
from src.utils.utils import click

if TYPE_CHECKING:
    # Only imported during static type checking, ignored at runtime
    from src.eve_ui.eve_ui import EveUI


class StationWindow:
    def __init__(self, eve_ui: 'EveUI', refresh_on_init=False):
        self.eve_ui: EveUI = eve_ui
        self.main_window_query = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            node_type="LobbyWnd",
            refresh_on_init=refresh_on_init
        )

        self.undock_btn_query = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            node_type="UndockButton",
            parent_query=self.main_window_query,
            refresh_on_init=refresh_on_init,
        )

    def is_docked(self):
        self.undock_btn_query.run()
        if self.undock_btn_query.result:
            return True
        return False

    def undock(self):
        if not self.undock_btn_query.run():
            return
        label = self.eve_ui.ui_tree.find_node(node_type="EveLabelMedium", root=self.undock_btn_query.result, refresh=False)
        if label.attrs.get("_setText") == "Abort Undock":
            return
        click(self.undock_btn_query.result)

    def click_logo(self):
        logo_icon = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            node_type="LogoIcon",
            parent_query=self.main_window_query,
        ).result

        if not logo_icon:
            return

        click(logo_icon)
