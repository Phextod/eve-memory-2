import time
from dataclasses import dataclass
from typing import List, Tuple

import keyboard
import pyautogui
import pyperclip

from src.eve_ui.context_menu import ContextMenu
from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree, UITreeNode
from src.utils.utils import drag_and_drop, click, MOUSE_RIGHT, get_path


@dataclass
class InventoryItem:
    id: int
    name: str
    quantity: int
    node: UITreeNode


class Inventory:
    def __init__(self, refresh_on_init=False):
        self.ui_tree: UITree = UITree.instance()
        self.context_menu: ContextMenu = ContextMenu.instance()

        self.main_window_query = BubblingQuery(
            node_type="InventoryPrimary",
            refresh_on_init=refresh_on_init,
        )

        self.item_components_query = BubblingQuery(
            node_type="InvItem",
            select_many=True,
            parent_query=self.main_window_query,
            refresh_on_init=refresh_on_init,
        )

        self.items: List[InventoryItem] = []
        self.capacity_max = 0
        self.capacity_filled = 0
        self.active_ship_hangar = None
        self.active_ship_drone_bay = None
        self.main_station_hangar = None
        self.station_containers = []

        self.update(refresh_on_init)

    def update_hangars(self, refresh=True):
        active_ship_container = BubblingQuery(
            node_type="TreeViewEntryInventoryCargo",
            parent_query=self.main_window_query,
            refresh_on_init=refresh,
        ).result
        if not active_ship_container:
            return

        self.active_ship_hangar = self.ui_tree.find_node(
            {'_name': 'topCont_ShipHangar'},
            root=active_ship_container,
            refresh=False,
        )

        self.active_ship_drone_bay = self.ui_tree.find_node(
            {'_name': 'topCont_ShipDroneBay'},
            root=active_ship_container,
            refresh=False,
        )
        if not self.active_ship_drone_bay:
            click(self.active_ship_hangar, MOUSE_RIGHT)
            if not self.context_menu.click_safe("Open Drone Bay"):
                click(self.active_ship_hangar)
            self.active_ship_drone_bay = self.ui_tree.find_node(
                {'_name': 'topCont_ShipDroneBay'},
                root=active_ship_container,
                refresh=False,
            )

        self.main_station_hangar = self.ui_tree.find_node(
            {'_name': 'topCont_ItemHangar'},
            root=self.main_window_query.result,
            refresh=refresh,
        )

        station_containers_containers = self.ui_tree.find_node(
            {'_name': 'topCont_StationContainer'},
            select_many=True,
            root=self.main_window_query.result,
            refresh=False
        )

        self.station_containers.clear()
        for container_container in station_containers_containers:
            container = self.ui_tree.find_node(node_type="TextBody", root=container_container)
            self.station_containers.append(container)

    def update_capacity(self, refresh=True):
        capacity_container = BubblingQuery(
            {'_name': 'capacityText'},
            parent_query=self.main_window_query,
            refresh_on_init=refresh
        ).result

        if capacity_container is None:
            self.capacity_filled = 0
            self.capacity_max = 0
            return

        capacity_text = capacity_container.attrs["_setText"]
        split = capacity_text.split(")")[-1].split("/")

        fill_text = "0"
        max_text = split[0]
        if len(split) == 2:
            fill_text = split[0]
            max_text = split[1]

        self.capacity_filled = float(fill_text.replace(" ", "").strip().replace(",", "."))
        self.capacity_max = float(max_text.replace(" ", "")[:-1].replace(",", "."))

    def update_items(self, refresh=True):
        self.items.clear()
        self.item_components_query.run(refresh)

        for item_node in self.item_components_query.result:
            # Additional info about items: data/itemTypes.csv or https://www.fuzzwork.co.uk/dump/latest/invTypes.csv
            # File is too big, so identify relevant items from their ids
            type_id = int(item_node.attrs.get("_name", "_").split("_")[1])
            if not type_id:
                continue

            name_node = self.ui_tree.find_node({'_name': 'itemNameLabel'}, root=item_node, refresh=False)
            name = name_node.attrs["_setText"].split(">")[-1]

            quantity = 1
            quantity_node_container = self.ui_tree.find_node({'_name': 'qtypar'}, root=item_node, refresh=False)
            if quantity_node_container:
                quantity_node = self.ui_tree.find_node(
                    node_type="EveLabelSmall",
                    root=quantity_node_container,
                    refresh=False
                )
                quantity_multiplier = 1
                quantity_text = quantity_node.attrs["_setText"].replace(" ", "")
                if "K" in quantity_text:
                    quantity_multiplier = 1_000
                    quantity_text = quantity_text.replace(",", ".").replace("K", "")
                elif "M" in quantity_text:
                    quantity_multiplier = 1_000_000
                    quantity_text = quantity_text.replace(",", ".").replace("M", "")
                quantity = int(float(quantity_text) * quantity_multiplier)

            self.items.append(InventoryItem(type_id, name, quantity, item_node))

    def update(self, refresh=True):
        self.update_hangars(refresh)
        self.update_capacity(refresh)
        self.update_items(refresh)

    @staticmethod
    def move_item(item_node: UITreeNode, target_node: UITreeNode, amount=None):
        if amount:
            pyautogui.keyDown("shiftleft")
            time.sleep(0.1)

        drag_and_drop(item_node.get_center(), target_node.get_center())

        if amount:
            pyautogui.keyUp("shiftleft")
            pyautogui.write(str(amount), interval=0.1)
            pyautogui.press("enter")

    def stack_all(self):
        btn_stack_all = BubblingQuery(
            {'_name': 'unique_UI_inventoryStackAll'},
            parent_query=self.main_window_query
        ).result

        if not btn_stack_all:
            return False

        click(btn_stack_all)
        return True

    def search_for(self, search_text):
        search_field = None
        while not search_field:
            search_field = BubblingQuery(
                {'_name': 'quickFilterInputBox'},
                parent_query=self.main_window_query
            ).result

        first_iter = True
        text_label = None
        while first_iter or text_label.attrs["_setText"] != search_text:
            first_iter = False
            pyperclip.copy(search_text)
            click(search_field)
            pyautogui.hotkey('ctrl', 'a', interval=0.1)
            pyautogui.hotkey('ctrl', 'v', interval=0.1)

            text_label = self.ui_tree.find_node(
                node_type="EveLabelMedium",
                root=search_field,
            )
        return True

    def loot_all(self):
        btn_loot_all = BubblingQuery({'_name': 'invLootAllBtn'}, self.main_window_query).result
        if not btn_loot_all:
            return False
        click(btn_loot_all)
        return True

    def repair_active_ship(self):
        click(self.active_ship_hangar, MOUSE_RIGHT)
        self.context_menu.click_safe("Get Repair Quote")
        time.sleep(0.5)

        repair_window = self.ui_tree.find_node(node_type="RepairShopWindow")

        no_result = self.ui_tree.find_node({'_name': 'noResultsContainer'}, root=repair_window, refresh=False)
        if not no_result:
            btn_group = self.ui_tree.find_node(node_type="ButtonGroup", root=repair_window, refresh=False)
            repair_all_btn = btn_group.find_image(get_path("images/repair_all.png"))
            click(repair_all_btn)
            pyautogui.press("enter")

        close_btn = self.ui_tree.find_node({'_name': 'CloseButtonIcon'}, root=repair_window, refresh=False)
        click(close_btn)
