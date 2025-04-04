from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree
from src.utils.utils import click


class StationWindow:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()
        self.main_window_query = BubblingQuery(node_type="LobbyWnd", refresh_on_init=refresh_on_init)
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
        if not self.undock_btn_query.run():
            return
        label = self.ui_tree.find_node(node_type="EveLabelMedium", root=self.undock_btn_query.result, refresh=False)
        if label.attrs.get("_setText") == "Abort Undock":
            return
        click(self.undock_btn_query.result)
