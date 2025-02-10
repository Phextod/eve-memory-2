from dataclasses import dataclass
from typing import List

from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree, UITreeNode


@dataclass
class Target:
    node: UITreeNode
    label_texts: List[str]
    is_active_target: bool


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
            labels = UITree.instance().find_node(node_type="EveLabelSmall", root=target_component, select_many=True)
            label_texts = [label.attrs["_setText"].split(">")[-1] for label in labels]
            active_target_marker = self.ui_tree.find_node(node_type="ActiveTargetOnBracket", root=target_component)
            self.targets.append(Target(target_component, label_texts, active_target_marker is not None))

        self.targets.sort(key=lambda t: t.node.x, reverse=True)

        return self

    def get_active_target(self):
        return next(t for t in self.targets if t.is_active_target)
