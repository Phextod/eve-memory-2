from typing import List, TYPE_CHECKING

from src.utils.bubbling_query import BubblingQuery
from src.utils.utils import click, wait_for_truthy

if TYPE_CHECKING:
    # Only imported during static type checking, ignored at runtime
    from src.eve_ui.eve_ui import EveUI


class Neocom:
    def __init__(self, eve_ui: 'EveUI', refresh_on_init=False):
        self.eve_ui: EveUI = eve_ui

        self.main_panel_query = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            query={'_name': 'l_abovemain'},
            refresh_on_init=refresh_on_init,
        )

    def open(self, path: List[str]):
        main_btn = self.eve_ui.ui_tree.find_node({'_name': 'eveMenuBtn'})
        click(main_btn)
        for menu_name in path:
            menu_btn = wait_for_truthy(
                lambda: BubblingQuery(
                    ui_tree=self.eve_ui.ui_tree,
                    query={'_setText': menu_name},
                    parent_query=self.main_panel_query,
                ).result,
                5
            )
            if menu_btn is None:
                return False
            click(menu_btn)
        return True
