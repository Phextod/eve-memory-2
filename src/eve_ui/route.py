import time
from typing import List

import pyautogui

from src import config
from src.eve_ui.context_menu import ContextMenu
from src.eve_ui.ship_ui import ShipUI, BuffNames
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
        self.util_menu_layer_query = BubblingQuery({'_name': 'l_utilmenu'}, refresh_on_init=refresh_on_init)

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
        while not BubblingQuery({'_setText': 'No Destination'}, parent_query=self.main_container_query).result:
            route_menu_btn = BubblingQuery(
                {'_texturePath': 'res:/UI/Texture/Classes/InfoPanels/Route.png'},
                parent_query=self.main_container_query
            ).result
            if not route_menu_btn:
                continue

            click(route_menu_btn)
            clear_waypoints_btn = BubblingQuery(
                {'_setText': 'Clear All Waypoints'},
                parent_query=self.util_menu_layer_query
            ).result
            if not clear_waypoints_btn:
                continue

            click(clear_waypoints_btn)

    def handle_modules_before_warp(self, activate_interdiction_nullifiers=False):
        self.ship_ui.update_modules()
        self.ship_ui.update_buffs()

        buff_names = [b.attrs.get("_name", "") for b in self.ship_ui.buff_buttons]
        if BuffNames.warp_disrupt.value in buff_names or BuffNames.warp_scramble.value in buff_names:
            for row, slot in config.AUTOPILOT_WARP_STABILIZER_MODULES:
                module_row = self.ship_ui.module_rows[row]
                if len(module_row) >= slot + 1:
                    module_row[slot].set_active(True)

        for row, slot in config.AUTOPILOT_MODULES_TO_ACTIVATE_BEFORE_WARP:
            module_row = self.ship_ui.module_rows[row]
            if len(module_row) >= slot + 1:
                module_row[slot].set_active(True)

        if activate_interdiction_nullifiers:
            for row, slot in config.AUTOPILOT_INTERDICTION_NULLIFIER_MODULES:
                module_row = self.ship_ui.module_rows[row]
                if len(module_row) >= slot + 1:
                    module_row[slot].set_active(True)

    def handle_modules_in_warp(self):
        self.ship_ui.update_modules()
        for row, slot in config.AUTOPILOT_MODULES_TO_ACTIVATE_BEFORE_WARP:
            module_row = self.ship_ui.module_rows[row]
            if len(module_row) < slot + 1:
                continue
            module_row[slot].set_active(False)

    def handle_modules_before_dock(self):
        self.ship_ui.update_modules()
        for row, slot in config.AUTOPILOT_MODULES_TO_ACTIVATE_BEFORE_DOCK:
            module_row = self.ship_ui.module_rows[row]
            if len(module_row) < slot + 1:
                continue
            module_row[slot].set_active(True)

    def autopilot(self, station_window: StationWindow, timers: Timers, accept_popups=True):
        # todo autopilot for routes not ending with docking
        self.handle_modules_before_warp()
        while True:
            is_docking = False
            clicked_command = False
            first_warp_attempt_time = None
            while not clicked_command or not self.ship_ui.update_speed().is_warping:
                self.update()
                if not self.route_sprites:
                    continue
                click(self.route_sprites[0], MOUSE_RIGHT)
                if self.context_menu.get_menu_btn("Approach", timeout=0):
                    continue
                wait_start = time.time()
                clicked_command = False
                should_refresh = False
                while not clicked_command and time.time() - wait_start < 0.75:
                    clicked_command = self.context_menu.click("Jump Through Stargate", refresh=should_refresh)
                    if not clicked_command:
                        is_docking = self.context_menu.click("Dock", refresh=False)
                        clicked_command = is_docking
                    should_refresh = True
                if clicked_command:
                    if not first_warp_attempt_time:
                        first_warp_attempt_time = time.time()
                    activate_interdiction_nullifiers = (
                            time.time() - first_warp_attempt_time > 10 and self.ship_ui.speed == 0
                    )
                    self.handle_modules_before_warp(activate_interdiction_nullifiers)
            self.ship_ui.click_center()

            wait_for_truthy(
                lambda: self.ship_ui.update_alert() and "Warp Drive Active" in self.ship_ui.indication_text,
                60
            )

            while not self.ship_ui.update_alert() or "Warp Drive Active" in self.ship_ui.indication_text:
                self.handle_modules_in_warp()

            if is_docking:
                self.handle_modules_before_dock()

            while not (TimerNames.jumpCloak.value in timers.update().timers or station_window.is_docked()):
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
