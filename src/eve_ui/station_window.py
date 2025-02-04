from src.utils.bubbling_query import BubblingQuery
from src.utils.interface import UITree
from src.utils.utils import click


class StationWindow:
    def __init__(self, ui_tree: UITree, refresh_on_init=False):
        self.ui_tree = ui_tree
        self.main_window_query = BubblingQuery(node_type="LobbyWnd", ui_tree=ui_tree, refresh_on_init=refresh_on_init)
        self.undock_btn_query = BubblingQuery(
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
        if self.is_docked():
            click(self.undock_btn_query.result)
