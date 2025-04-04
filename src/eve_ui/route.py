import time
from typing import List

import pyautogui

from src.eve_ui.context_menu import ContextMenu
from src.eve_ui.ship_ui import ShipUI
from src.eve_ui.station_window import StationWindow
from src.eve_ui.timers import Timers, TimerNames
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITreeNode, UITree
from src.utils.utils import MOUSE_RIGHT, click, wait_for_truthy


class Route:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()
        self.context_menu: ContextMenu = ContextMenu.instance()
        self.ship_ui: ShipUI = ShipUI.instance()

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

    def autopilot(self, station_window: StationWindow, timers: Timers, accept_popups=True):
        # todo autopilot for routes not ending with docking
        while True:
            while not self.ship_ui.update_speed().is_warping:
                self.update()
                click(self.route_sprites[0], MOUSE_RIGHT)
                if self.context_menu.get_menu_btn("Approach", timeout=0):
                    continue
                wait_start = time.time()
                clicked_command = False
                should_refresh = False
                while not clicked_command and time.time() - wait_start < 1:
                    clicked_command = self.context_menu.click("Jump Through Stargate", refresh=should_refresh)
                    clicked_command = clicked_command or self.context_menu.click("Dock", refresh=False)
                    should_refresh = True
            self.ship_ui.click_center()

            while not (station_window.is_docked() or TimerNames.jumpCloak.value in timers.update().timers):
                time.sleep(1)

                if not accept_popups:
                    continue
                message_box = self.ui_tree.find_node(node_type="MessageBox")
                if message_box:
                    checkbox = self.ui_tree.find_node(node_type="Checkbox", root=message_box, refresh=False)
                    if checkbox:
                        click(checkbox)
                    pyautogui.press("enter")

            if station_window.is_docked():
                return True
