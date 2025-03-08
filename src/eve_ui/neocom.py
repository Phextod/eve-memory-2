from typing import List

from src.utils.bubbling_query import BubblingQuery
from src.utils.singleton import Singleton
from src.utils.ui_tree import UITree
from src.utils.utils import click, wait_for_truthy


@Singleton
class Neocom:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()

        self.main_panel_query = BubblingQuery(
            {'_name': 'l_abovemain'},
            refresh_on_init=refresh_on_init,
        )

    def open(self, path: List[str]):
        main_btn = self.ui_tree.find_node({'_name': 'eveMenuBtn'})
        click(main_btn)
        for menu_name in path:
            menu_btn = wait_for_truthy(
                lambda: BubblingQuery(
                    {'_setText': menu_name},
                    parent_query=self.main_panel_query,
                ).result,
                5
            )
            if menu_btn is None:
                return False
            click(menu_btn)
        return True
