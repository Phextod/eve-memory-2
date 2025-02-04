from enum import Enum
from typing import Dict

import pyautogui

from src.utils.bubbling_query import BubblingQuery
from src.utils.interface import UITree, UITreeNode
from src.utils.utils import click


class ShipModule:
    class ActiveStatus(Enum):
        not_activatable = 0
        not_active = 1
        active = 2
        turning_off = 3

    class OverloadStatus(Enum):
        not_overloadable = 0
        not_overloaded = 1
        overloaded = 2
        turning_off = 3

    def __init__(self, slot_node: UITreeNode, ui_tree: UITree):
        self.slot_node = slot_node

        icon = ui_tree.find_node(node_type="Icon", root=slot_node, refresh=False)
        self.module_type = icon.attrs["_texturePath"].split("/")[-1].split(".")[0]

        # Cloaks and some other modules are active but not overloadable. If you care about those improve this part
        overload_button = ui_tree.find_node({'_name': 'overloadBtn'}, root=slot_node, refresh=False)
        if "Disabled" not in overload_button.attrs["_texturePath"]:
            module_button = ui_tree.find_node(node_type="ModuleButton", root=slot_node, refresh=False)
            if module_button.attrs.get("ramp_active", None):
                glow = ui_tree.find_node({"_texturePath": "Glow"}, contains=True, root=slot_node, refresh=False)
                if glow.attrs["_color"]["rPercent"] >= 100:
                    self.active_status = ShipModule.ActiveStatus.turning_off
                else:
                    self.active_status = ShipModule.ActiveStatus.active
            else:
                self.active_status = ShipModule.ActiveStatus.not_active
        else:
            self.active_status = ShipModule.ActiveStatus.not_activatable

        if "Disabled" in overload_button.attrs["_texturePath"]:
            self.overload_status = ShipModule.OverloadStatus.not_overloadable
        elif "OverloadOff" in overload_button.attrs["_texturePath"]:
            self.overload_status = ShipModule.OverloadStatus.not_overloaded
        elif overload_button.attrs['_color']['aPercent'] >= 100:
            self.overload_status = ShipModule.OverloadStatus.overloaded
        else:
            self.overload_status = ShipModule.OverloadStatus.turning_off

    def set_active(self, activate: bool):
        if (activate and self.active_status == ShipModule.ActiveStatus.not_active) or \
                (not activate and self.active_status == ShipModule.ActiveStatus.active):
            click(self.slot_node)

    def set_overload(self, overload: bool):
        if (overload and self.overload_status == ShipModule.OverloadStatus.not_overloaded) or \
                (not overload and self.overload_status == ShipModule.OverloadStatus.overloaded):
            pyautogui.keyDown("shift")
            click(self.slot_node)
            pyautogui.keyUp("shift")


class ShipUI:
    def __init__(self, ui_tree: UITree, refresh_on_init=False):
        self.ui_tree = ui_tree

        self.main_container_query = BubblingQuery(node_type="ShipUI", ui_tree=ui_tree, refresh_on_init=refresh_on_init)

        self.high_modules: Dict[int, ShipModule] = dict()
        self.medium_modules: Dict[int, ShipModule] = dict()
        self.low_modules: Dict[int, ShipModule] = dict()
        self.update_modules(refresh_on_init)

        self.capacitor_percent = 0.0
        self.update_capacitor_percent(refresh_on_init)

    def update_capacitor_percent(self, refresh=True):
        capacitor_sprites = BubblingQuery(
            {"_texturePath": "capacitorCell_2"},
            self.main_container_query,
            contains=True,
            select_many=True,
            refresh_on_init=refresh,
        ).result

        sprite_alphas = [c.attrs["_color"]["aPercent"] for c in capacitor_sprites]
        count_0 = sprite_alphas.count(0)

        if sprite_alphas:
            self.capacitor_percent = count_0 / len(sprite_alphas)
        else:
            self.capacitor_percent = 0.0

    def update_high_slots(self, refresh=True):
        self.high_modules.clear()
        modules_nodes = BubblingQuery(
            {'_name': 'inFlightHighSlot'},
            self.main_container_query,
            select_many=True,
            contains=True,
            refresh_on_init=refresh,
        ).result
        modules_nodes.sort(key=lambda a: a.x)
        for module_index, slot in enumerate(modules_nodes):
            # module_index = int(slot.attrs["_name"].replace("inFlightMediumSlot", ""))
            ship_module = ShipModule(slot, self.ui_tree)
            self.high_modules.update({module_index: ship_module})

    def update_medium_slots(self, refresh=True):
        self.medium_modules.clear()
        modules_nodes = BubblingQuery(
            {'_name': 'inFlightMediumSlot'},
            self.main_container_query,
            select_many=True,
            contains=True,
            refresh_on_init=refresh,
        ).result
        modules_nodes.sort(key=lambda a: a.x)
        for module_index, slot in enumerate(modules_nodes):
            # module_index = int(slot.attrs["_name"].replace("inFlightMediumSlot", ""))
            ship_module = ShipModule(slot, self.ui_tree)
            self.medium_modules.update({module_index: ship_module})

    def update_low_slots(self, refresh=True):
        self.low_modules.clear()
        modules_nodes = BubblingQuery(
            {'_name': 'inFlightLowSlot'},
            self.main_container_query,
            select_many=True,
            contains=True,
            refresh_on_init=refresh,
        ).result
        modules_nodes.sort(key=lambda a: a.x)
        for module_index, slot in enumerate(modules_nodes):
            # module_index = int(slot.attrs["_name"].replace("inFlightMediumSlot", ""))
            ship_module = ShipModule(slot, self.ui_tree)
            self.low_modules.update({module_index: ship_module})

    def update_modules(self, refresh=True):
        self.update_high_slots(refresh=refresh)
        self.update_medium_slots(refresh=False)
        self.update_low_slots(refresh=False)
