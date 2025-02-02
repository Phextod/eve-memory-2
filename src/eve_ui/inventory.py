import time
from typing import List, Tuple

import pyautogui

from src.utils.bubbling_query import BubblingQuery
from src.utils.interface import UITree, UITreeNode
from src.utils.utils import left_click


class Inventory:
    def __init__(self, ui_tree: UITree):
        self.ui_tree = ui_tree

        self.main_window_query = BubblingQuery(node_type="InventoryPrimary", ui_tree=ui_tree)

        self.item_components_query = BubblingQuery(
            node_type="InvItem",
            select_many=True,
            parent_query=self.main_window_query,
        )

        # {item_id: item_node}
        self.items: List[Tuple[int, UITreeNode]] = []
        self.capacity_max = 0
        self.capacity_filled = 0
        self.active_ship_hangar = None
        self.main_station_hangar = None
        self.station_containers = []

        self.update_hangars()
        self.update_capacity()
        self.update_items()

    def update_hangars(self):
        active_ship_container = BubblingQuery(
            node_type="TreeViewEntryInventoryCargo",
            parent_query=self.main_window_query
        ).result

        self.active_ship_hangar = self.ui_tree.find_node(
            node_type="TextBody",
            root=active_ship_container
        )

        self.main_station_hangar = self.ui_tree.find_node(
            {'_name': 'topCont_ItemHangar'},
            root=self.main_window_query.result
        )

        station_containers_containers = self.ui_tree.find_node(
            {'_name': 'topCont_StationContainer'},
            select_many=True,
            root=self.main_window_query.result,
        )

        self.station_containers.clear()
        for container_container in station_containers_containers:
            container = self.ui_tree.find_node(node_type="TextBody", root=container_container)
            self.station_containers.append(container)

    def update_capacity(self):
        capacity_container = BubblingQuery(
            {'_name': 'capacityText'},
            parent_query=self.main_window_query
        ).result

        capacity_text = capacity_container.attrs["_setText"]
        split = capacity_text.split("/")

        fill_text = "0"
        max_text = split[0]
        if len(split) == 2:
            fill_text = split[0]
            max_text = split[1]

        self.capacity_filled = float(fill_text.replace(" ", "").strip().replace(",", "."))
        self.capacity_max = float(max_text.replace(" ", "")[:-1].replace(",", "."))

    def update_items(self):
        self.items.clear()
        self.item_components_query.run()

        for item_node in self.item_components_query.result:
            # Additional info about items: https://www.fuzzwork.co.uk/dump/latest/invItems.csv
            # File is too big, so identify relevant items from their ids
            type_id = int(item_node.attrs["_name"].split("_")[1])
            self.items.append((type_id, item_node))

    @staticmethod
    def move_item(item_node, target_node):
        left_click(item_node)
        time.sleep(1)
        left_click(target_node)

    def stack_all(self):
        btn_stack_all = BubblingQuery(
            {'_name': 'unique_UI_inventoryStackAll'},
            parent_query=self.main_window_query
        )
        left_click(btn_stack_all.result)

    def search_for(self, search_text):
        search_field = BubblingQuery(
            {'_name': 'quickFilterInputBox'},
            parent_query=self.main_window_query
        )
        left_click(search_field.result)
        pyautogui.hotkey('ctrl', 'a', interval=0.2)
        pyautogui.write(search_text, interval=0.25)
