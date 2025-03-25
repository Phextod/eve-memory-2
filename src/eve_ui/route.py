import time
from typing import List

from src.eve_ui.context_menu import ContextMenu
from src.eve_ui.ship_ui import ShipUI
from src.eve_ui.station_window import StationWindow
from src.eve_ui.timers import Timers, TimerNames
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITreeNode, UITree
from src.utils.utils import MOUSE_RIGHT, click, wait_for_truthy


class Route:
    def __init__(self, refresh_on_init=False):
        self.context_menu: ContextMenu = ContextMenu.instance()
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

    def clear(self):
        if not self.route_sprites:
            return

        click(self.route_sprites[0], MOUSE_RIGHT)
        self.context_menu.click_safe("Set Destination")
        click(self.route_sprites[0], MOUSE_RIGHT)
        self.context_menu.click_safe("Remove Waypoint")

    def autopilot(self, station_window: StationWindow, timers: Timers):
        # todo autopilot for routes not ending with docking
        context_menu: ContextMenu = ContextMenu.instance()

        while True:
            is_jumping = False
            is_docking = False
            while not (is_docking or is_jumping):
                self.update()
                click(self.route_sprites[0], MOUSE_RIGHT)
                time.sleep(0.5)
                is_jumping = context_menu.click("Jump Through Stargate")
                is_docking = context_menu.click("Dock")

            if is_jumping:
                if wait_for_truthy(lambda: TimerNames.jumpCloak.value in timers.update().timers, 120):
                    continue
                else:
                    break
            else:
                if wait_for_truthy(lambda: station_window.is_docked(), 60):
                    return True
                break

        return False
