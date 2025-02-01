from dataclasses import dataclass, field
from typing import List, Optional

from src.utils.interface import UITree, UITreeNode


@dataclass
class NodeSelector:
    query: dict = field(default=None)
    address: int = field(default=None)
    node_type: str = field(default=None)
    select_many: bool = field(default=False)
    contains: bool = field(default=False)
    root: UITreeNode = field(default=None)

    def find(self, ui_tree: UITree, refresh=True):
        return ui_tree.find_node(
            query=self.query,
            address=self.address,
            node_type=self.node_type,
            select_many=self.select_many,
            contains=self.contains,
            root=self.root,
            refresh=refresh,
        )


class UIComponent:
    def __init__(
            self,
            selector: NodeSelector,
            ui_tree: UITree = None,
            parent: "UIComponent" = None,
    ):
        self.selector: NodeSelector = selector
        self.ui_tree = ui_tree
        self.parent: UIComponent = parent

        # Duplicate only for readability. Maybe this is just confusing
        self.node: Optional[UITreeNode] = None
        self.nodes: List[UITreeNode] = []

        if parent:
            self.ui_tree = parent.ui_tree

        self.update_node()

    def update_node(self):
        self.node = None
        self.nodes.clear()

        nodes = self.selector.find(self.ui_tree)

        if not nodes and self.parent:
            self.parent.update_node()
            self.selector.root = self.parent.node
            nodes = self.selector.find(self.ui_tree, refresh=False)

        if isinstance(nodes, list):
            self.nodes = nodes
        else:
            self.node = nodes

        return nodes
