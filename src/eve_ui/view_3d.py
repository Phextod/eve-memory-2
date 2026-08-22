from src.utils import utils
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree


class View3d:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()
        self.main_overlay_query = BubblingQuery(node_type="Toggled3DViewWarning", refresh_on_init=refresh_on_init)

    def is_3d_view_enabled(self):
        if self.main_overlay_query.run():
            return False
        return True

    @staticmethod
    def toggle_3d_view():
        utils.hold_and_release_keys(['ctrl', 'shift', 'f9'])
