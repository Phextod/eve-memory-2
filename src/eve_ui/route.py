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

    def first_sprite_dock_or_jump(self, timeout=0.75):
        self.update()
        if not self.route_sprites:
            return False, False

        click(self.route_sprites[0], MOUSE_RIGHT)

        clicked_command = False
        is_docking = False
        wait_start = time.time()
        while not clicked_command:
            clicked_command = self.context_menu.click("Jump Through Stargate")
            if not clicked_command:
                is_docking = self.context_menu.click("Dock")
                clicked_command = is_docking

            if time.time() - wait_start > timeout:
                break

        return clicked_command, is_docking

    def autopilot(self, station_window: StationWindow, timers: Timers, accept_popups=True):
        # todo autopilot for routes not ending with docking
        self.handle_modules_before_warp()
        while True:
            is_docking = False
            clicked_command = False
            first_warp_attempt_time = None
            while not clicked_command or not self.ship_ui.update_speed().is_warping:
                clicked_command = False
                while not clicked_command:
                    clicked_command, is_docking = self.first_sprite_dock_or_jump(timeout=0.75)

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
                while not station_window.is_docked():
                    self.handle_modules_before_dock()
                    self.first_sprite_dock_or_jump(timeout=0.75)
                return True

            while TimerNames.jumpCloak.value not in timers.update().timers:
                if not accept_popups:
                    continue
                message_box = self.ui_tree.find_node(node_type="MessageBox")
                if message_box:
                    checkbox = self.ui_tree.find_node(node_type="Checkbox", root=message_box, refresh=False)
                    if checkbox:
                        click(checkbox)
                    pyautogui.press("enter")
