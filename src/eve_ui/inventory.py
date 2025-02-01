from typing import Dict

from src.eve_ui.ui_component import UIComponent, NodeSelector
from src.utils.interface import UITree, UITreeNode


class Inventory(UIComponent):
    def __init__(self, ui_tree: UITree):
        super().__init__(NodeSelector(node_type="InventoryPrimary"), ui_tree)

        self.ship_hangar = UIComponent(NodeSelector({'_name': 'ShipHangar'}, select_many=True), parent=self)
        self.item_hangar = UIComponent(NodeSelector({'_name': 'ShipHangar'}, select_many=True), parent=self)

        self.item_components = UIComponent(NodeSelector(node_type="InvItem", select_many=True), parent=self)
        self.items: Dict[int, UITreeNode] = dict()

    def update(self):
        self.items.clear()
        self.item_components.update_node()

        for item_node in self.item_components.nodes:
            # Additional info about items: https://www.fuzzwork.co.uk/dump/latest/invItems.csv
            # File is too big, so identify relevant items from their ids
            type_id = int(item_node.attrs["_name"].split("_")[1])
            self.items.update({type_id: item_node})

        print(self.items)

