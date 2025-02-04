from dataclasses import dataclass
from typing import List

from src.utils.bubbling_query import BubblingQuery
from src.utils.interface import UITree


@dataclass
class Target:
    name: str


class TargetBar:
    def __init__(self, refresh_on_init=False):
        self.main_window_query = BubblingQuery({"_name": "l_target"}, refresh_on_init=refresh_on_init)

        self.target_components_query = BubblingQuery(
            node_type="TargetInBar",
            select_many=True,
            parent_query=self.main_window_query,
            refresh_on_init=refresh_on_init,
        )

        self.targets: List[Target] = []

    def update(self):
        self.targets.clear()

        self.target_components_query.run()

        for target_component in self.target_components_query.result:
            labels = UITree.instance().find_node(node_type="EveLabelSmall", root=target_component, select_many=True)
            name = " ".join([text.attrs["_setText"] for text in labels])
            self.targets.append(Target(name))
