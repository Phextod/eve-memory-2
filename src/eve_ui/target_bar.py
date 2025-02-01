from dataclasses import dataclass
from typing import List

from src.eve_ui.ui_component import UIComponent, NodeSelector
from src.utils.interface import UITree


@dataclass
class Target:
    name: str


class TargetBar(UIComponent):
    def __init__(self, ui_tree: UITree):
        super().__init__(NodeSelector({"_name": "l_target"}), ui_tree)

        self.target_components = UIComponent(
            NodeSelector(node_type="TargetInBar", select_many=True),
            parent=self
        )

        self.targets: List[Target] = []

    def update(self):
        self.targets.clear()

        self.target_components.update_node()

        for target_component in self.target_components.nodes:
            labels = self.ui_tree.find_node(node_type="EveLabelSmall", root=target_component, select_many=True)
            name = " ".join([text.attrs["_setText"] for text in labels])
            self.targets.append(Target(name))
