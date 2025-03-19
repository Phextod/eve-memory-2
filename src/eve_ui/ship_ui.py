import math
import time
from enum import Enum
from typing import Dict, List

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

    latest_state_change_times = dict()
    latest_overload_state_change_times = dict()
    WAIT_TIME_ON_STATE_CHANGE = 1.5

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

        damage_state_cont = ui_tree.find_node(node_type="DamageStateCont", root=node, refresh=False)
        if damage_state_cont:
            heat_dmg_str = damage_state_cont.attrs['_hint'][:-1].split(" ")[1].replace(",", ".")
            self.heat_damage = float(heat_dmg_str) / 100
        else:
            self.heat_damage = 0.0

        glow = ui_tree.find_node(
            {"_texturePath": "Glow"},
            contains=True,
            root=node,
            refresh=False,
        )
        self.is_repairing = glow is not None and glow.attrs['_color']['rPercent'] == 0

        # Cloaks and some other modules are active but not overloadable. If you care about those improve this part
        overload_button = ui_tree.find_node({'_name': 'overloadBtn'}, root=node, refresh=False)
        if "Disabled" not in overload_button.attrs["_texturePath"]:
            module_button = ui_tree.find_node(node_type="ModuleButton", root=node, refresh=False)
            if module_button.attrs.get("ramp_active", None):
                if glow and glow.attrs["_color"]["rPercent"] >= 100:
                    self.active_status = ShipModule.ActiveStatus.turning_off
                else:
                    self.active_status = ShipModule.ActiveStatus.active
            else:
                left_ramp = ui_tree.find_node({'_name': 'leftRamp'}, root=node, refresh=False)
                right_ramp = ui_tree.find_node({'_name': 'rightRamp'}, root=node, refresh=False)
                ramp_displayed = False
                if left_ramp and right_ramp:
                    left_rotation = float(left_ramp.attrs.get("_rotation", 0.0))
                    right_rotation = float(right_ramp.attrs.get("_rotation", 0.0))
                    ramp_displayed = (
                        not math.isclose(left_rotation, math.pi, abs_tol=1e-06)
                        or not math.isclose(right_rotation, math.pi, abs_tol=1e-06)
                    )
                if ramp_displayed:
                    self.active_status = ShipModule.ActiveStatus.reloading
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

    def set_state_change_time(self):
        ShipModule.latest_state_change_times.update({self.node.attrs['_name']: time.time()})

    def set_active(self, activate: bool):
        if (
            time.time() - ShipModule.latest_state_change_times.get(self.node.attrs['_name'], 0.0)
                < ShipModule.WAIT_TIME_ON_STATE_CHANGE
        ):
            return False

        if (activate and self.active_status == ShipModule.ActiveStatus.not_active) or \
                (not activate and self.active_status == ShipModule.ActiveStatus.active):
            click(self.node)
            self.set_state_change_time()
            return True
        return False

    def set_overload(self, overload: bool):
        if (
            time.time() - ShipModule.latest_overload_state_change_times.get(self.node.attrs['_name'], 0.0)
                < ShipModule.WAIT_TIME_ON_STATE_CHANGE
        ):
            return False

        if (overload and self.overload_status == ShipModule.OverloadStatus.not_overloaded) or \
                (not overload and self.overload_status == ShipModule.OverloadStatus.overloaded):
            pyautogui.keyDown("shift")
            click(self.node)
            pyautogui.keyUp("shift")
            ShipModule.latest_overload_state_change_times.update({self.node.attrs['_name']: time.time()})


class ShipUI:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()
        self.main_container_query = BubblingQuery(node_type="ShipUI", refresh_on_init=refresh_on_init)

        self.high_modules: Dict[int, ShipModule] = dict()
        self.medium_modules: Dict[int, ShipModule] = dict()
        self.low_modules: Dict[int, ShipModule] = dict()
        self.capacitor_percent = 0.0
        self.buff_buttons: List[UITreeNode] = []

        self.is_warping = False
        self.speed: float = 0.0

        self.indication_text = ""

        self.shield_percent: float = 0.0
        self.armor_percent: float = 0.0
        self.structure_percent: float = 0.0

        self.hud_readout_query = BubblingQuery(
            node_type="HudReadout",
            parent_query=self.main_container_query,
            refresh_on_init=False
        )

        self.is_readout_open = False
        if not self.hud_readout_query.result and self.main_container_query.result:
            self.display_readouts()
            self.is_readout_open = True

        self.update(refresh_on_init)

    def display_readouts(self):
        util_menu = self.ui_tree.find_node(node_type="UtilMenu", root=self.main_container_query.result, refresh=False)
        click(util_menu)
        readout_btn = self.ui_tree.find_node({'_setText': 'Display Readout'})
        click(readout_btn)
        click(util_menu)

    def update_hp(self, refresh=True):
        if not self.is_readout_open:
            if self.hud_readout_query.run():
                self.is_readout_open = True
            elif self.main_container_query.result:
                self.display_readouts()
                self.is_readout_open = True
            else:
                return

        containers = BubblingQuery(
            node_type="ContainerAutoSize",
            parent_query=self.hud_readout_query,
            select_many=True,
            refresh_on_init=refresh
        ).result
        if containers is None:
            return

        for container in containers:
            label = self.ui_tree.find_node(node_type="EveLabelSmall", root=container, refresh=False)
            percent = int(label.attrs.get("_setText", "0").split("%")[0]) / 100
            name = container.attrs["_name"]
            if name == "shield":
                self.shield_percent = percent
            elif name == "armor":
                self.armor_percent = percent
            elif name == "structure":
                self.structure_percent = percent

    def update_capacitor_percent(self, refresh=True):
        capacitor_sprites = BubblingQuery(
            {"_texturePath": "capacitorCell_2"},
            self.main_container_query,
            contains=True,
            select_many=True,
            refresh_on_init=refresh,
        ).result
        if capacitor_sprites is None:
            self.capacitor_percent = 0.0
            return

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
        return self

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
        return self

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
        return self

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

        self.buff_buttons += BubblingQuery(
            node_type="OffensiveBuffButton",
            parent_query=self.main_container_query,
            select_many=True,
            refresh_on_init=False
        ).result
        return self

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
        self.update_hp(refresh)

        return self

    def full_speed(self):
        btn_full_speed = BubblingQuery(node_type="MaxSpeedButton", parent_query=self.main_container_query).result
        click(btn_full_speed)

    def click_center(self):
        capacitor_container = BubblingQuery(
            node_type="CapacitorContainer",
            parent_query=self.main_container_query
        ).result

        if not capacitor_container:
            return

        click(capacitor_container)

    def get_modules(self):
        return (
            [m for i, m in self.high_modules.items()]
            + [m for j, m in self.medium_modules.items()]
            + [m for k, m in self.low_modules.items()]
        )
