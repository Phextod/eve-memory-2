from dataclasses import dataclass
from typing import List

from src.utils.bubbling_query import BubblingQuery
from src.utils.interface import UITree


@dataclass
class Target:
    name: str


class TargetBar:
    def __init__(self, ui_tree: UITree):
        self.ui_tree = ui_tree

        self.main_window_query = BubblingQuery({"_name": "l_target"}, ui_tree=ui_tree)

        self.target_components_query = BubblingQuery(
            node_type="TargetInBar",
            select_many=True,
            parent_query=self.main_window_query
        )

        self.targets: List[Target] = []

    def update(self):
        self.targets.clear()

        self.target_components_query.run()

        for target_component in self.target_components_query.result:
            labels = self.ui_tree.find_node(node_type="EveLabelSmall", root=target_component, select_many=True)
            name = " ".join([text.attrs["_setText"] for text in labels])
            self.targets.append(Target(name))
