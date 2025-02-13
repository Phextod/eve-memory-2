from typing import List

from src.eve_ui.context_menu import ContextMenu
from src.eve_ui.ship_ui import ShipUI
from src.eve_ui.timers import Timers, TimerNames
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITreeNode, UITree
from src.utils.utils import MOUSE_RIGHT, click, wait_for_truthy


class Route:
    def __init__(self, refresh_on_init=False):
        self.main_container_query = BubblingQuery(node_type="InfoPanelRoute", refresh_on_init=refresh_on_init)

        self.route_sprites: List[UITreeNode] = []
        self.update(False)

    def update(self, refresh=True):
        self.route_sprites.clear()

        icons = BubblingQuery(
            node_type="AutopilotDestinationIcon",
            parent_query=self.main_container_query,
            select_many=True,
            refresh_on_init=refresh,
        ).result

        ui_tree: UITree = UITree.instance()
        for icon in icons:
            sprite = ui_tree.find_node(node_type="Sprite", root=icon, refresh=False)
            self.route_sprites.append(sprite)

        self.route_sprites.sort(key=lambda a: (a.x, a.y))

        return self

    def autopilot(self, ship_ui: ShipUI, timers: Timers):
        context_menu: ContextMenu = ContextMenu.instance()

        self.update()
        click(self.route_sprites[0], MOUSE_RIGHT)

        is_jumping = False
        is_docking = False
        while not is_docking and not is_jumping:
            is_jumping = context_menu.click("Jump through stargate")
            is_docking = context_menu.click("Dock")

        click(self.route_sprites[0], MOUSE_RIGHT)

        while is_jumping and context_menu.click_safe("Jump through stargate", 5):
            if not wait_for_truthy(lambda: TimerNames.jumpCloak.value in timers.update().timers, 60):
                return False
            self.update()
            if self.route_sprites:
                click(self.route_sprites[0], MOUSE_RIGHT)
            else:
                return False

        if context_menu.click_safe("Dock", 5):
            wait_for_truthy(lambda: ship_ui.update().main_container_query.result is None, 60)
            return True

        return False


