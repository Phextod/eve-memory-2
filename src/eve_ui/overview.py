from dataclasses import dataclass
from typing import List, Dict

from src.utils.bubbling_query import BubblingQuery
from src.utils.interface import UITree


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


class Overview:
    def __init__(self, ui_tree: UITree, refresh_on_init=False):
        self.ui_tree = ui_tree
        self.main_window_query = BubblingQuery(
            node_type="OverviewWindow",
            ui_tree=ui_tree,
            refresh_on_init=refresh_on_init,
        )

        self.entries: List[Dict[str, str]] = []
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

        self.update_headers(refresh_on_init)
        self.update_entries(refresh_on_init)

    def update_headers(self, refresh=True):
        self.headers.clear()

        headers = self.header_component_query.run()
        headers.sort(key=lambda a: a.x)

        for header in headers:
            label = self.ui_tree.find_node(node_type="EveLabelSmall", root=header, refresh=refresh)
            text = label.attrs["_setText"] if label else "Icon"
            self.headers.append(text)

    def update_entries(self, refresh=True):
        self.entries.clear()

        if not self.headers:
            self.update_headers(refresh)

        entry_nodes = self.entry_component_query.run(refresh)

        for entry_node in entry_nodes:
            entry_labels = [self.ui_tree.nodes[label_address] for label_address in entry_node.children]
            entry_labels.sort(key=lambda a: a.x)

            entry = dict()
            for header, entry_label in zip(self.headers, entry_labels):
                value = entry_label.attrs.get("_text") or entry_label.attrs.get("_bgTexturePath")
                entry.update({header: value})

            self.entries.append(entry)
