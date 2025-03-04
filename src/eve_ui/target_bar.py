from dataclasses import dataclass
from typing import List

from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree, UITreeNode


@dataclass
class Target:
    node: UITreeNode
    name: str
    distance: int
    is_active_target: bool
    active_weapon_icons: List[UITreeNode]

    @staticmethod
    def from_component_node(target_component):
        ui_tree: UITree = UITree.instance()

        labels = ui_tree.find_node(node_type="EveLabelSmall", root=target_component, select_many=True, refresh=False)
        labels.sort(key=lambda l: l.y)

        label_texts = [label.attrs["_setText"].split(">")[-1] for label in labels]
        name = " ".join(label_texts[:-1])
        distance = 100_000
        if label_texts:
            distance_text = label_texts[-1].replace(" ", "")
            distance_multiplier = 0
            if "km" in distance_text:
                distance_multiplier = 1_000
                distance_text = distance_text.replace("km", "")
            elif "m" in distance_text:
                distance_multiplier = 1
                distance_text = distance_text.replace("m", "")

            distance = int(distance_text) * distance_multiplier

        active_target_marker = ui_tree.find_node(
            node_type="ActiveTargetOnBracket",
            root=target_component,
            refresh=False
        )
        is_active_target = active_target_marker is not None

        active_weapon_container = ui_tree.find_node(node_type="Weapon", root=target_component, refresh=False)
        active_weapon_icons = []
        if active_weapon_container:
            active_weapon_icons = ui_tree.find_node(
                node_type="Icon",
                root=active_weapon_container,
                select_many=True,
                refresh=False
            )

        return Target(target_component, name, distance, is_active_target, active_weapon_icons)


class TargetBar:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()
        self.main_window_query = BubblingQuery({"_name": "l_target"}, refresh_on_init=refresh_on_init)

        self.targets: List[Target] = []

        self.update(refresh_on_init)

    def update(self, refresh=True):
        self.targets.clear()

        target_components = BubblingQuery(
            node_type="TargetInBar",
            select_many=True,
            parent_query=self.main_window_query,
            refresh_on_init=refresh,
        ).result

        for target_component in target_components:
            self.targets.append(Target.from_component_node(target_component))

        self.targets.sort(key=lambda t: t.node.x, reverse=True)

        return self

    def get_active_target(self):
        return next((t for t in self.targets if t.is_active_target), None)
