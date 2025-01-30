from dataclasses import dataclass
from typing import List

from src.utils.interface import UITree


@dataclass
class Target:
    name: str


class TargetBar:
    def __init__(self, ui_tree: UITree):
        self.targets: List[Target] = []

        self.ui_tree = ui_tree
        self.main_container = ui_tree.find_node({"_name": "l_target"})

    def update(self):
        self.targets.clear()

        target_components = self.ui_tree.find_node(
            node_type="TargetInBar",
            root=self.main_container,
            select_many=True,
            refresh=True,
        )

        for target_component in target_components:
            labels = self.ui_tree.find_node(node_type="EveLabelSmall", root=target_component, select_many=True)
            name = " ".join([text.attrs["_setText"] for text in labels])
            self.targets.append(Target(name))

