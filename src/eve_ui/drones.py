import copy
from dataclasses import dataclass
from enum import Enum
from typing import List

import pyautogui

from src.eve_ui.context_menu import ContextMenu
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree, UITreeNode
from src.utils.utils import click, MOUSE_RIGHT, wait_for_truthy


class DroneStatus(Enum):
    idle = 0
    fighting = 1
    returning = 2


@dataclass
class Drone:
    entry_node: UITreeNode
    name: str
    shield_percent: float
    armor_percent: float
    structure_percent: float
    status: DroneStatus
    quantity: int

    @staticmethod
    def from_entry_node(entry_node, ui_tree):
        type_node = ui_tree.find_node(
            {'_name': 'entryLabel'},
            root=entry_node,
            refresh=False,
        )
        name = type_node.attrs.get("_setText").split(" <")[0]

        quantity = int(name.split("(")[1].replace(")", "")) if "(" in name else 1
        if quantity > 1:
            name = name.split(" (")[0]

        struct_gauge = ui_tree.find_node({'_name': 'structGauge'}, root=entry_node, refresh=False)
        struct_fill = ui_tree.find_node(node_type="Fill", root=struct_gauge, refresh=False)
        structure_percent = struct_fill.attrs["_displayWidth"] / struct_gauge.attrs["_displayWidth"]

        armor_gauge = ui_tree.find_node({'_name': 'armorGauge'}, root=entry_node, refresh=False)
        armor_fill = ui_tree.find_node(node_type="Fill", root=armor_gauge, refresh=False)
        armor_percent = armor_fill.attrs["_displayWidth"] / armor_gauge.attrs["_displayWidth"]

        shield_gauge = ui_tree.find_node({'_name': 'shieldGauge'}, root=entry_node, refresh=False)
        shield_fill = ui_tree.find_node(node_type="Fill", root=shield_gauge, refresh=False)
        shield_percent = shield_fill.attrs["_displayWidth"] / shield_gauge.attrs["_displayWidth"]

        status = DroneStatus.idle
        status_split = type_node.attrs.get("_setText").split(">")
        if len(status_split) > 1:
            status_text = status_split[1].split("<")[0]
            if status_text == "Fighting":
                status = DroneStatus.fighting
            elif status_text == "Returning":
                status = DroneStatus.returning

        return Drone(
            entry_node=entry_node,
            name=name,
            shield_percent=shield_percent,
            armor_percent=armor_percent,
            structure_percent=structure_percent,
            status=status,
            quantity=quantity,
        )


class Drones:
    def __init__(self, refresh_on_init=False):
        self.main_window_query = BubblingQuery(
            node_type="DronesWindow",
            refresh_on_init=refresh_on_init
        )

        self.drone_entries_query = BubblingQuery(
            {'_name': 'entry_'},
            contains=True,
            select_many=True,
            parent_query=self.main_window_query,
            refresh_on_init=refresh_on_init,
        )

        self.in_bay: List[Drone] = []
        self.in_space: List[Drone] = []
        self.update(refresh=refresh_on_init)

    def update(self, refresh=True):
        self.in_bay.clear()
        self.in_space.clear()

        self.drone_entries_query.run(refresh)

        for entry_node in self.drone_entries_query.result:
            if "NoDroneIn" in entry_node.type:
                continue
            drone = Drone.from_entry_node(entry_node, UITree.instance())
            if drone.quantity == 1:
                if entry_node.type == "DroneInSpaceEntry":
                    self.in_space.append(drone)
                elif entry_node.type == "DroneInBayEntry":
                    self.in_bay.append(drone)
            else:
                for _ in range(drone.quantity):
                    copy_drone = copy.deepcopy(drone)
                    copy_drone.quantity = 1
                    if entry_node.type == "DroneInSpaceEntry":
                        self.in_space.append(copy_drone)
                    elif entry_node.type == "DroneInBayEntry":
                        self.in_bay.append(copy_drone)

        return self

    @staticmethod
    def launch_drones(drones: List[Drone]):
        drones.sort(key=lambda d: d.entry_node.y, reverse=True)
        for drone in drones:
            click(drone.entry_node, MOUSE_RIGHT, pos_x=0.2)
            ContextMenu.instance().click_safe("Launch Drone", 5)

    @staticmethod
    def recall(drone: Drone):
        click(drone.entry_node, MOUSE_RIGHT, pos_x=0.1)
        ContextMenu.instance().click_safe("Return to Drone Bay", 5)

    @staticmethod
    def recall_all():
        pyautogui.hotkey('shift', 'r', interval=0.2)

    def safe_recall_all(self):
        self.recall_all()
        wait_for_truthy(lambda: self.update and not self.in_space, 30)

    @staticmethod
    def attack_target():
        pyautogui.press('f')
