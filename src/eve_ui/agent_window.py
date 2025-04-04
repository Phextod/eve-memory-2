from src.eve_ui.context_menu import ContextMenu
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree
from src.utils.utils import get_path, click, MOUSE_RIGHT


class AgentWindow:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()
        self.context_menu: ContextMenu = ContextMenu.instance()
        self.main_window_query = BubblingQuery(
            node_type="AgentDialogueWindow",
            refresh_on_init=refresh_on_init,
        )

        self.button_group_query = BubblingQuery(
            node_type="ButtonGroup",
            parent_query=self.main_window_query,
        )

    def get_button(self, btn_text):
        self.button_group_query.run(True)
        return BubblingQuery(
            {'_setText': btn_text},
            node_type="EveLabelMedium",
            parent_query=self.button_group_query,
        ).result

    def add_drop_off_waypoint(self):
        location_link_1 = BubblingQuery(
            {'_name': 'tablecell 1-3'},
            parent_query=self.main_window_query,
        ).result
        click(location_link_1, MOUSE_RIGHT, pos_y=0.3)

        self.context_menu.click_safe("Add Waypoint")

    def add_pickup_waypoint(self):
        location_link_1 = BubblingQuery(
            {'_name': 'tablecell 0-3'},
            parent_query=self.main_window_query,
        ).result
        click(location_link_1, MOUSE_RIGHT, pos_y=0.3)

        self.context_menu.click_safe("Add Waypoint")
