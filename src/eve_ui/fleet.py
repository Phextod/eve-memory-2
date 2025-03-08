from src.eve_ui.context_menu import ContextMenu
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree
from src.utils.utils import click, MOUSE_RIGHT


class Fleet:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()
        self.context_menu: ContextMenu = ContextMenu.instance()
        self.main_layer_query = BubblingQuery({'_name': 'l_main'}, refresh_on_init=refresh_on_init)
        self.main_window_query = BubblingQuery(node_type="FleetWindow", parent_query=self.main_layer_query)

    def is_in_fleet(self):
        click(self.main_layer_query.result, MOUSE_RIGHT)
        self.context_menu.open_submenu("Pilot", contains=True)

        form_fleet_btn = None
        fleet_submenu = None
        while not form_fleet_btn and not fleet_submenu:
            form_fleet_btn = BubblingQuery(
                {'_setText': "Form Fleet"},
                self.context_menu.menu_container_query,
                contains=True,
            ).result

            fleet_submenu = BubblingQuery(
                {'_setText': "Fleet"},
                self.context_menu.menu_container_query,
            ).result

        if form_fleet_btn:
            return False
        return True

    def form_fleet_with_self(self):
        click(self.main_layer_query.result, MOUSE_RIGHT)
        self.context_menu.open_submenu("Pilot", contains=True)

        form_fleet_btn = None
        fleet_submenu = None
        while not form_fleet_btn and not fleet_submenu:
            form_fleet_btn = BubblingQuery(
                {'_setText': "Form Fleet"},
                self.context_menu.menu_container_query,
                contains=True,
            ).result

            fleet_submenu = BubblingQuery(
                {'_setText': "Fleet"},
                self.context_menu.menu_container_query,
            ).result

        if form_fleet_btn is None:
            return

        self.context_menu.click_safe("Form Fleet", contains=True)

    def leave_fleet(self):
        click(self.main_layer_query.result, MOUSE_RIGHT)
        self.context_menu.open_submenu("Pilot", contains=True)

        form_fleet_btn = None
        fleet_submenu = None
        while not form_fleet_btn and not fleet_submenu:
            form_fleet_btn = BubblingQuery(
                {'_setText': "Form Fleet"},
                self.context_menu.menu_container_query,
                contains=True,
            ).result

            fleet_submenu = BubblingQuery(
                {'_setText': "Fleet"},
                self.context_menu.menu_container_query,
            ).result

        if fleet_submenu is None:
            return

        self.context_menu.click_safe("Fleet")
        self.context_menu.click_safe("Leave Fleet")
        self.context_menu.click_safe("Confirm")

    def close_fleet_window(self):
        self.main_window_query.run()
        if not self.main_window_query.result:
            return

        close_btn = self.ui_tree.find_node({'_name': 'CloseButtonIcon'}, root=self.main_window_query.result)
        click(close_btn)
