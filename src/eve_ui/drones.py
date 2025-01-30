from dataclasses import dataclass

from src.utils.interface import UITree, UITreeNode


@dataclass
class Drone:
    entry_node: UITreeNode
    name: str
    shield_percent: float
    armor_percent: float
    structure_percent: float

    @staticmethod
    def from_entry_node(entry_node, ui_tree):
        type_node = ui_tree.find_node(
            {'_name': 'entryLabel'},
            root=entry_node,
        )
        name = type_node.attrs.get("_setText").split("<")[0]

        struct_gauge = ui_tree.find_node({'_name': 'structGauge'}, root=entry_node)
        struct_fill = ui_tree.find_node(node_type="Fill", root=struct_gauge)
        structure_percent = struct_fill.attrs["_displayWidth"] / struct_gauge.attrs["_displayWidth"]

        armor_gauge = ui_tree.find_node({'_name': 'armorGauge'}, root=entry_node)
        armor_fill = ui_tree.find_node(node_type="Fill", root=armor_gauge)
        armor_percent = armor_fill.attrs["_displayWidth"] / armor_gauge.attrs["_displayWidth"]

        shield_gauge = ui_tree.find_node({'_name': 'shieldGauge'}, root=entry_node)
        shield_fill = ui_tree.find_node(node_type="Fill", root=shield_gauge)
        shield_percent = shield_fill.attrs["_displayWidth"] / shield_gauge.attrs["_displayWidth"]

        return Drone(
            entry_node=entry_node,
            name=name,
            shield_percent=shield_percent,
            armor_percent=armor_percent,
            structure_percent=structure_percent,
        )


class Drones:
    def __init__(self, ui_tree: UITree):
        self.ui_tree = ui_tree

        self.drones_window = None
        self.update_drones_window()

        self.in_bay = []
        self.in_space = []
        self.update()

    def update_drones_window(self):
        self.drones_window = self.ui_tree.find_node(
            node_type="DronesWindow",
        )

    def update(self):
        self.in_bay.clear()
        self.in_space.clear()

        drone_entries = self.ui_tree.find_node(
            {'_name': 'entry_'},
            contains=True,
            select_many=True,
            root=self.drones_window,
            refresh=True
        )

        for entry_node in drone_entries:
            if entry_node.type == "DroneInSpaceEntry":
                self.in_space.append(Drone.from_entry_node(entry_node, self.ui_tree))
            elif entry_node.type == "DroneInBayEntry":
                self.in_bay.append(Drone.from_entry_node(entry_node, self.ui_tree))
