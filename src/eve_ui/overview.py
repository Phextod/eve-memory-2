from typing import List, Dict

from src.utils.interface import UITree, UITreeNode
from src.utils.utils import wait_for_truthy


class Overview:
    def __init__(self, ui_tree: UITree):
        self.ui_tree = ui_tree
        self.overview_window = ui_tree.find_node(node_type="OverviewWindow", refresh=True)

        self.entries: List[Dict[str, str]] = []
        self.headers = []

        self.update_headers()
        self.update()

    def update_headers(self):
        self.headers.clear()

        headers = self.ui_tree.find_node(node_type="Header", root=self.overview_window, select_many=True)
        headers.sort(key=lambda a: a.x)

        for header in headers:
            label = self.ui_tree.find_node(node_type="EveLabelSmall", root=header)
            text = label.attrs["_setText"] if label else "Icon"
            self.headers.append(text)

    def update(self):
        self.entries.clear()

        entry_nodes = self.ui_tree.find_node(
            node_type="OverviewScrollEntry",
            root=self.overview_window,
            refresh=True,
            select_many=True
        )

        for entry_node in entry_nodes:
            entry_labels = [self.ui_tree.nodes[label_address] for label_address in entry_node.children]
            entry_labels.sort(key=lambda a: a.x)

            entry = dict()
            for header, entry_label in zip(self.headers, entry_labels):
                value = entry_label.attrs.get("_text") or entry_label.attrs.get("_bgTexturePath")
                entry.update({header: value})

            self.entries.append(entry)
