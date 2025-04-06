from typing import List

from src.eve_ui.context_menu import ContextMenu
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree, UITreeNode
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
            refresh_on_init=refresh_on_init,
        )

        self.left_pane_query = BubblingQuery(
            {'_name': 'leftPane'},
            parent_query=self.main_window_query,
            refresh_on_init=refresh_on_init
        )

        self.right_pane_query = BubblingQuery(
            {'_name': 'rightPane'},
            parent_query=self.main_window_query,
            refresh_on_init=refresh_on_init
        )

        self.left_pane_html_container_query = BubblingQuery(
            node_type="Edit",
            parent_query=self.left_pane_query,
            refresh_on_init=refresh_on_init,
        )

        self.right_pane_html_container_query = BubblingQuery(
            node_type="Edit",
            parent_query=self.right_pane_query,
            refresh_on_init=refresh_on_init,
        )

        self.left_pane_html_content = ""
        self.right_pane_html_content = ""
        self.button_labels: List[UITreeNode] = []

        self.update(refresh_on_init)

    def update(self, refresh=True):
        self.update_buttons(refresh)
        self.update_html_content(refresh)
        return self

    def update_buttons(self, refresh=True):
        self.button_group_query.run(refresh)
        self.button_labels = BubblingQuery(
            node_type="EveLabelMedium",
            parent_query=self.button_group_query,
            select_many=True,
        ).result
        return self

    def update_html_content(self, refresh=True):
        if self.left_pane_query.run(refresh) and self.left_pane_html_container_query.run(refresh):
            self.left_pane_html_content = self.left_pane_html_container_query.result.attrs.get("_sr", "")
        else:
            self.left_pane_html_content = ""

        if self.right_pane_query.run(refresh) and self.right_pane_html_container_query.run(refresh):
            self.right_pane_html_content = self.right_pane_html_container_query.result.attrs.get("_sr", "")
        else:
            self.right_pane_html_content = ""

        return self

    def get_effective_standing(self):
        key_string = "Effective Standing: "
        start = self.left_pane_html_content.find(key_string)
        if start == -1:
            return 0
        start += len(key_string)
        end = self.left_pane_html_content.find(" ", start)
        return float(self.left_pane_html_content[start:end].replace(",", '.'))

    def get_rewards(self):
        key_string_isk = " ISK"
        start_isk = self.right_pane_html_content.find(key_string_isk)
        key_string_lp = " Loyalty Points"

    def get_button(self, btn_text):
        for button_label in self.button_labels:
            if button_label.attrs.get("_setText", "") == btn_text:
                return button_label
        return None

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
