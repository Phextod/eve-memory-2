from dataclasses import dataclass
from typing import List, Dict

from src.eve_ui.ui_component import UIComponent, NodeSelector
from src.utils.interface import UITree, UITreeNode
from src.utils.utils import wait_for_truthy


@dataclass
class OverviewEntry:
    icon: str
    distance: str
    name: str
    type: str
    tag: str
    corporation: str
    alliance: str
    faction: str
    militia: str
    size: str
    velocity: str
    radial_velocity: str
    transversal_velocity: str
    angular_velocity: str

    @staticmethod
    def decode(in_data: dict):
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
            "radial_velocity": "Radial Velocity",
            "transversal_velocity": "Transversal Velocity",
            "angular_velocity": "Angular Velocity",
        }

        out_data = dict()
        for out_key in decode_dict:
            in_key = decode_dict[out_key]
            out_data.update({out_key: in_data.get(in_key, None)})

        return out_data


class Overview(UIComponent):
    def __init__(self, ui_tree: UITree):
        super().__init__(NodeSelector(node_type="OverviewWindow"), ui_tree)

        self.entries: List[Dict[str, str]] = []
        self.headers = []

        self.header_component = UIComponent(
            NodeSelector(node_type="Header", select_many=True),
            parent=self
        )

        self.entry_component = UIComponent(
            NodeSelector(node_type="OverviewScrollEntry", select_many=True),
            parent=self
        )

        self.update_headers()
        self.update()

    def update_headers(self):
        self.headers.clear()

        headers = self.header_component.update_node()
        headers.sort(key=lambda a: a.x)

        for header in headers:
            label = self.ui_tree.find_node(node_type="EveLabelSmall", root=header)
            text = label.attrs["_setText"] if label else "Icon"
            self.headers.append(text)

    def update(self):
        self.entries.clear()

        entry_nodes = self.entry_component.update_node()

        for entry_node in entry_nodes:
            entry_labels = [self.ui_tree.nodes[label_address] for label_address in entry_node.children]
            entry_labels.sort(key=lambda a: a.x)

            entry = dict()
            for header, entry_label in zip(self.headers, entry_labels):
                value = entry_label.attrs.get("_text") or entry_label.attrs.get("_bgTexturePath")
                entry.update({header: value})

            self.entries.append(entry)
