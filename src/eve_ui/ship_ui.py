import math
from enum import Enum
from typing import Dict

import pyautogui

from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree, UITreeNode
from src.utils.utils import click


class ShipModule:
    class ActiveStatus(Enum):
        not_activatable = 0
        not_active = 1
        active = 2
        turning_off = 3
        reloading = 4

    class OverloadStatus(Enum):
        not_overloadable = 0
        not_overloaded = 1
        overloaded = 2
        turning_off = 3

    def __init__(self, node: UITreeNode):
        ui_tree: UITree = UITree.instance()
        self.node = node

        icon = ui_tree.find_node(node_type="Icon", root=node, refresh=False)
        self.module_type = icon.attrs["_texturePath"].split("/")[-1].split(".")[0]
        self.ammo_count = 0
        ammo_parent = ui_tree.find_node({'_name': 'quantityParent'}, root=node, refresh=False)
        if ammo_parent:
            number_containers = ui_tree.find_node(node_type="Label", root=ammo_parent, refresh=False, select_many=True)
            number_containers.sort(key=lambda n: n.x, reverse=True)
            self.ammo_count = int(number_containers[0].attrs.get('_setText', ""))

        # Cloaks and some other modules are active but not overloadable. If you care about those improve this part
        overload_button = ui_tree.find_node({'_name': 'overloadBtn'}, root=node, refresh=False)
        if "Disabled" not in overload_button.attrs["_texturePath"]:
            module_button = ui_tree.find_node(node_type="ModuleButton", root=node, refresh=False)
            if module_button.attrs.get("ramp_active", None):
                glow = ui_tree.find_node(
                    {"_texturePath": "Glow"},
                    contains=True,
                    root=node,
                    refresh=False,
                )
                if glow.attrs["_color"]["rPercent"] >= 100:
                    self.active_status = ShipModule.ActiveStatus.turning_off
                else:
                    self.active_status = ShipModule.ActiveStatus.active
            else:
                self.active_status = ShipModule.ActiveStatus.not_active
        else:
            left_ramp = ui_tree.find_node({'_name': 'leftRamp'}, root=node, refresh=False)
            right_ramp = ui_tree.find_node({'_name': 'rightRamp'}, root=node, refresh=False)
            ramp_displayed = False
            if left_ramp and right_ramp:
                left_rotation = float(left_ramp.attrs.get("_rotation", 0.0))
                right_rotation = float(right_ramp.attrs.get("_rotation", 0.0))
                ramp_displayed = math.isclose(left_rotation, math.pi, abs_tol=1e-06) \
                                 or math.isclose(right_rotation, math.pi, abs_tol=1e-06)
            if ramp_displayed:
                self.active_status = ShipModule.ActiveStatus.reloading
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
            click(self.node)

    def set_overload(self, overload: bool):
        if (overload and self.overload_status == ShipModule.OverloadStatus.not_overloaded) or \
                (not overload and self.overload_status == ShipModule.OverloadStatus.overloaded):
            pyautogui.keyDown("shift")
            click(self.node)
            pyautogui.keyUp("shift")


class ShipUI:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()
        self.main_container_query = BubblingQuery(node_type="ShipUI", refresh_on_init=refresh_on_init)

        self.high_modules: Dict[int, ShipModule] = dict()
        self.medium_modules: Dict[int, ShipModule] = dict()
        self.low_modules: Dict[int, ShipModule] = dict()
        self.capacitor_percent = 0.0
        self.buff_buttons = []

        self.is_warping = False
        self.speed: float = 0.0

        self.indication_text = ""

        self.update(refresh_on_init)

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
            ship_module = ShipModule(slot)
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
            ship_module = ShipModule(slot)
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
            ship_module = ShipModule(slot)
            self.low_modules.update({module_index: ship_module})

    def update_modules(self, refresh=True):
        self.update_high_slots(refresh=refresh)
        self.update_medium_slots(refresh=False)
        self.update_low_slots(refresh=False)
        return self

    def update_buffs(self, refresh=True):
        self.buff_buttons = BubblingQuery(
            node_type="BuffButton",
            parent_query=self.main_container_query,
            select_many=True,
            refresh_on_init=refresh
        ).result

    def update_alert(self, refresh=True):
        indication_container = BubblingQuery(
            {'_name': 'indicationContainer'},
            parent_query=self.main_container_query,
            refresh_on_init=refresh
        ).result

        caption = self.ui_tree.find_node(node_type="CaptionLabel", root=indication_container, refresh=False)
        line2 = self.ui_tree.find_node({'_name': 'indicationtext2'}, root=indication_container, refresh=False)
        if caption and line2:
            self.indication_text = f"{caption.attrs['_setText']} - {line2.attrs['_setText'].split('>')[-1]}"
        else:
            self.indication_text = ""

    def update_speed(self, refresh=True):
        speed_label_node = BubblingQuery(
            {'_name': 'speedLabel'},
            parent_query=self.main_container_query,
            refresh_on_init=refresh
        ).result

        self.is_warping = False
        self.speed = 0.0

        if not speed_label_node:
            return

        if "Warping" in speed_label_node.attrs["_setText"]:
            self.is_warping = True
        else:
            self.speed = float(speed_label_node.attrs["_setText"].split(" ")[0])

        return self

    def update(self, refresh=True):
        self.update_modules(refresh)
        self.update_capacitor_percent(refresh)
        self.update_buffs(refresh)
        self.update_alert(refresh)
        self.update_speed(refresh)

        return self

    def full_speed(self):
        btn_full_speed = BubblingQuery(node_type="MaxSpeedButton", parent_query=self.main_container_query).result
        click(btn_full_speed)
