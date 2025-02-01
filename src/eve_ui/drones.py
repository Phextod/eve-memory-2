from dataclasses import dataclass

from src.eve_ui.ui_component import UIComponent, NodeSelector
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


class Drones(UIComponent):
    def __init__(self, ui_tree: UITree):
        super().__init__(NodeSelector(node_type="DronesWindow"), ui_tree)

        self.drone_entries = UIComponent(
            NodeSelector({'_name': 'entry_'}, contains=True, select_many=True),
            parent=self
        )

        self.in_bay = []
        self.in_space = []
        self.update()

    def update(self):
        self.in_bay.clear()
        self.in_space.clear()

        self.drone_entries.update_node()

        for entry_node in self.drone_entries.nodes:
            if entry_node.type == "DroneInSpaceEntry":
                self.in_space.append(Drone.from_entry_node(entry_node, self.ui_tree))
            elif entry_node.type == "DroneInBayEntry":
                self.in_bay.append(Drone.from_entry_node(entry_node, self.ui_tree))
