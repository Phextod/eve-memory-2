from src.utils.bubbling_query import BubblingQuery
from src.utils.interface import UITree
from src.utils.utils import click


class ContextMenu:
    def __init__(self, ui_tree: UITree, refresh_on_init=False):
        self.ui_tree = ui_tree

        self.menu_container_query = BubblingQuery({'_name': 'l_menu'}, ui_tree=ui_tree, refresh_on_init=refresh_on_init)

    def click(self, entry_text):
        target = BubblingQuery(
            {'_setText': entry_text},
            self.menu_container_query
        ).result

        if target:
            click(target)
            return True
        return False
