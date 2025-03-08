from src.eve_ui.context_menu import ContextMenu
from src.eve_ui.neocom import Neocom
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree
from src.utils.utils import click, MOUSE_RIGHT, wait_for_truthy


class Fleet:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()
        self.neocom: Neocom = Neocom.instance()
        self.context_menu: ContextMenu = ContextMenu.instance()

        self.main_window_query = BubblingQuery(node_type="FleetWindow", refresh_on_init=refresh_on_init)

    def is_in_fleet(self):
        if not self.main_window_query.run():
            self.neocom.open(["Social", "Fleet"])

        form_fleet_btn = None
        fleet_header = None
        while form_fleet_btn is None and fleet_header is None:
            form_fleet_btn = BubblingQuery({'_setText': 'Form Fleet'}, parent_query=self.main_window_query).result
            fleet_header = BubblingQuery(node_type="FleetHeader", parent_query=self.main_window_query).result

        if form_fleet_btn is None:
            return True
        return False

    def form_fleet(self):
        if not self.main_window_query.run():
            self.neocom.open(["Social", "Fleet"])

        form_fleet_btn = wait_for_truthy(
            lambda: BubblingQuery({'_setText': 'Form Fleet'}, parent_query=self.main_window_query).result,
            2
        )

        if form_fleet_btn is None:
            return False

        click(form_fleet_btn)
        return True

    def leave_fleet(self):
        if not self.main_window_query.run():
            self.neocom.open(["Social", "Fleet"])

        fleet_header = wait_for_truthy(
            lambda: BubblingQuery(node_type="FleetHeader", parent_query=self.main_window_query).result,
            2
        )

        if fleet_header is None:
            return

        click(fleet_header, MOUSE_RIGHT)
        self.context_menu.click_safe("Leave Fleet")
        self.context_menu.click_safe("Confirm")

    def close_fleet_window(self):
        if not self.main_window_query.run():
            return

        close_btn = self.ui_tree.find_node({'_name': 'CloseButtonIcon'}, root=self.main_window_query.result)
        click(close_btn)
