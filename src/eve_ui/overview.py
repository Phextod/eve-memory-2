from dataclasses import dataclass
from enum import Enum
from typing import List

import pyautogui

from src.eve_ui.context_menu import ContextMenu, DistancePresets
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree, UITreeNode
from src.utils.utils import click, MOUSE_RIGHT


@dataclass
class OverviewEntry:
    icon: str = None
    distance: str = None
    name: str = None
    type: str = None
    tag: str = None
    corporation: str = None
    alliance: str = None
    faction: str = None
    militia: str = None
    size: str = None
    velocity: str = None
    radial_velocity: str = None
    transversal_velocity: str = None
    angular_velocity: str = None

    is_targeted_by_me = False
    is_active_target = False
    is_being_targeted = False
    is_only_targeting = False

    node: UITreeNode = None

    class Action(Enum):
        unlock_target = "Unlock Target"
        approach = "Approach"
        open_cargo = "Open Cargo"
        activate_gate = "Activate Gate"

    @staticmethod
    def from_entry_node(entry_node: UITreeNode, headers: list):
        decode_dict = {
            "icon": "Icon",
            "distance": "Distance",
            "name": "Name",
            "type": "Type",
            "tag": "Tag",
            "corporation": "Corporation",
            "alliance": "Alliance",
            "faction": "Faction",
            "militia": "Militia",
            "size": "Size",
            "velocity": "Velocity",
            "radial_velocity": "Radial Velocity (m/s)",
            "transversal_velocity": "Transversal Velocity (m/s)",
            "angular_velocity": "Angular Velocity (deg/s)",
        }
        ui_tree: UITree = UITree.instance()

        entry_labels = ui_tree.find_node(
            node_type="OverviewLabel",
            root=entry_node,
            select_many=True,
            refresh=False,
        )
        icon = ui_tree.find_node({'_name': 'iconSprite'}, root=entry_node, refresh=False)
        if icon:
            entry_labels.append(icon)
        entry_labels.sort(key=lambda a: a.x)

        entry_dict = dict()
        for header, entry_label in zip(headers, entry_labels):
            value = entry_label.attrs.get("_text") or entry_label.attrs.get("_texturePath")
            entry_dict.update({header: value})

        decoded_data = dict()
        for out_key in decode_dict:
            in_key = decode_dict[out_key]
            decoded_data.update({out_key: entry_dict.get(in_key, None)})

        entry = OverviewEntry(**decoded_data)

        active_target_node = ui_tree.find_node(
            {'_name': 'myActiveTargetIndicator'},
            root=entry_node,
            refresh=False,
        )
        entry.is_active_target = active_target_node is not None

        targeted_by_me_node = ui_tree.find_node(
            {'_name': 'targetedByMeIndicator'},
            root=entry_node,
            refresh=False,
        )
        entry.is_targeted_by_me = targeted_by_me_node is not None

        targeting_node = ui_tree.find_node({'_name': 'targeting'}, root=entry_node, refresh=False)
        entry.is_being_targeted = targeting_node is not None

        hostile_bracket = ui_tree.find_node({'_name': 'hostile'}, root=entry_node, refresh=False)
        if hostile_bracket:
            bracket_color = hostile_bracket.attrs["_color"]
            entry.is_only_targeting = (
                bracket_color["rPercent"] == 100
                and bracket_color["gPercent"] == 80
                and bracket_color["bPercent"] == 0
            )
        else:
            entry.is_only_targeting = False

        entry.node = entry_node
        entry.ui_tree = ui_tree

        return entry

    def generic_action(self, action: Action):
        click(self.node, MOUSE_RIGHT)
        return ContextMenu.instance().click_safe(action.value, 5)

    def target(self):
        pyautogui.keyDown("ctrl")
        click(self.node)
        pyautogui.keyUp("ctrl")

    def orbit(self, distance=0):
        click(self.node, MOUSE_RIGHT)
        distance_text = "Orbit"
        if distance > 0:
            ContextMenu.instance().open_submenu(distance_text, contains=True)
            distance_text = DistancePresets.closest(distance)["text"]
        return ContextMenu.instance().click_safe(distance_text, 5)


class Overview:
    def __init__(self, refresh_on_init=False):
        self.main_window_query = BubblingQuery(
            node_type="OverviewWindow",
            refresh_on_init=refresh_on_init,
        )

        self.entries: List[OverviewEntry] = []
        self.headers = []

        self.header_component_query = BubblingQuery(
            node_type="Header",
            select_many=True,
            parent_query=self.main_window_query,
            refresh_on_init=refresh_on_init,
        )

        self.entry_component_query = BubblingQuery(
            node_type="OverviewScrollEntry",
            select_many=True,
            parent_query=self.main_window_query,
            refresh_on_init=refresh_on_init,
        )

        self.update(refresh_on_init)

    def update_headers(self, refresh=True):
        self.headers.clear()

        headers = self.header_component_query.run()
        if not headers:
            return

        headers.sort(key=lambda a: a.x)

        for header in headers:
            label = UITree.instance().find_node(node_type="EveLabelSmall", root=header, refresh=refresh)
            text = label.attrs["_setText"] if label else "Icon"
            self.headers.append(text)

        return self

    def update(self, refresh=True):
        self.entries.clear()

        if not self.update_headers(refresh):
            return self

        entry_nodes = self.entry_component_query.run(refresh)

        for entry_node in entry_nodes[::-1]:
            self.entries.append(OverviewEntry.from_entry_node(entry_node, self.headers))

        self.entries.sort(key=lambda e: e.node.y)

        return self
