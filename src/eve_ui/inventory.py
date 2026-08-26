import time
from dataclasses import dataclass
from typing import List, TYPE_CHECKING

import pyautogui
import pyperclip

from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITreeNode
from src.utils.utils import drag_and_drop, click, MOUSE_RIGHT, wait_for_truthy

if TYPE_CHECKING:
    # Only imported during static type checking, ignored at runtime
    from src.eve_ui.eve_ui import EveUI


@dataclass
class InventoryItem:
    id: int
    name: str
    quantity: int
    node: UITreeNode


class Inventory:
    def __init__(self, eve_ui: 'EveUI', refresh_on_init=False, do_setup=True):
        self.eve_ui: EveUI = eve_ui
        self.currently_selected_tab_text = ""
        self.currently_selected_tab_index = -1

        self.main_window_query = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            node_type="InventoryPrimary",
            refresh_on_init=refresh_on_init,
        )

        self.item_components_query = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
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

        if do_setup:
            self.setup(refresh_on_init)

        self.update(refresh_on_init)

    def setup(self, refresh):
        active_ship_container = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            node_type="TreeViewEntryInventoryCargo",
            parent_query=self.main_window_query,
            refresh_on_init=refresh,
        ).result
        if not active_ship_container:
            return

        self.active_ship_hangar = self.eve_ui.ui_tree.find_node(
            {'_name': 'topCont_ShipHangar'},
            root=active_ship_container,
            refresh=False,
        )

        self.active_ship_drone_bay = self.eve_ui.ui_tree.find_node(
            {'_name': 'topCont_ShipDroneBay'},
            root=active_ship_container,
            refresh=False,
        )
        if not self.active_ship_drone_bay:
            click(self.active_ship_hangar, MOUSE_RIGHT)
            if not self.eve_ui.context_menu.click_safe("Open Drone Bay"):
                click(self.active_ship_hangar)

    def update_hangars(self, refresh=True):
        active_ship_container = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            node_type="TreeViewEntryInventoryCargo",
            parent_query=self.main_window_query,
            refresh_on_init=refresh,
        ).result
        if not active_ship_container:
            return self

        self.active_ship_hangar = self.eve_ui.ui_tree.find_node(
            {'_name': 'topCont_ShipHangar'},
            root=active_ship_container,
            refresh=False,
        )

        self.active_ship_drone_bay = self.eve_ui.ui_tree.find_node(
            {'_name': 'topCont_ShipDroneBay'},
            root=active_ship_container,
            refresh=False,
        )

        self.main_station_hangar = self.eve_ui.ui_tree.find_node(
            {'_name': 'topCont_ItemHangar'},
            root=self.main_window_query.result,
            refresh=refresh,
        )

        station_containers_containers = self.eve_ui.ui_tree.find_node(
            {'_name': 'topCont_StationContainer'},
            select_many=True,
            root=self.main_window_query.result,
            refresh=False
        )
        self.station_containers.clear()
        for container_container in station_containers_containers:
            container = self.eve_ui.ui_tree.find_node(node_type="TextBody", root=container_container)
            self.station_containers.append(container)

        inventory_tabs_text_bodies = self.eve_ui.ui_tree.find_node(
            node_type='TextBody',
            root=self.main_window_query.result,
            select_many=True,
            refresh=False,
        )
        inventory_tabs_text_bodies.sort(key=lambda x: x.y)
        self.currently_selected_tab_index, self.currently_selected_tab_text = next(
            ((i, x.attrs.get('_setText', "")) for i, x in enumerate(inventory_tabs_text_bodies)
             if x.attrs.get('_color') and x.attrs['_color'].get('aPercent', 0) == 90),
            (-1, "")
        )

        return self

    def update_capacity(self, refresh=True):
        capacity_container = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            query={'_name': 'capacityText'},
            parent_query=self.main_window_query,
            refresh_on_init=refresh
        ).result

        if capacity_container is None:
            self.capacity_filled = 0
            self.capacity_max = 0
            return self

        capacity_text = capacity_container.attrs["_setText"]
        split = capacity_text.split(")")[-1].split("/")

        fill_text = "0"
        max_text = split[0]
        if len(split) == 2:
            fill_text = split[0]
            max_text = split[1]

        self.capacity_filled = float(fill_text.replace(" ", "").strip().replace(",", "."))
        self.capacity_max = float(max_text.replace(" ", "")[:-1].replace(",", "."))

        return self

    def update_items(self, refresh=True):
        self.items.clear()
        self.item_components_query.run(refresh)

        for item_node in self.item_components_query.result:
            # Additional info about items: data/itemTypes.csv or https://www.fuzzwork.co.uk/dump/latest/invTypes.csv
            # File is too big, so identify relevant items from their ids
            type_id = int(item_node.attrs.get("_name", "_").split("_")[1])
            if not type_id:
                continue

            name_node = self.eve_ui.ui_tree.find_node({'_name': 'itemNameLabel'}, root=item_node, refresh=False)
            if not name_node:
                continue
            name = name_node.attrs.get("_setText","").split(">")[-1]

            quantity = 1
            quantity_node_container = self.eve_ui.ui_tree.find_node({'_name': 'qtypar'}, root=item_node, refresh=False)
            if quantity_node_container:
                quantity_node = self.eve_ui.ui_tree.find_node(
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
            ui_tree=self.eve_ui.ui_tree,
            query={'_name': 'unique_UI_inventoryStackAll'},
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
                ui_tree=self.eve_ui.ui_tree,
                query={'_name': 'quickFilterInputBox'},
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

            text_label = self.eve_ui.ui_tree.find_node(
                node_type="EveLabelMedium",
                root=search_field,
            )
        return

    def smart_search(self, item_name):
        item = next((i for i in self.items if i.name == item_name), None)
        if not item:
            search_field = wait_for_truthy(
                lambda: BubblingQuery(
                    ui_tree=self.eve_ui.ui_tree,
                    query={'_name': 'quickFilterInputBox'},
                    parent_query=self.main_window_query
                ).result,
                5
            )
            if not search_field:
                return None
            search_label = self.eve_ui.ui_tree.find_node(node_type="EveLabelMedium", root=search_field, refresh=False)
            search_label_text = search_label.attrs.get("_setText", None)
            if search_label_text != item_name:
                self.search_for(item_name)
            self.update_items()
            item = next((i for i in self.items if i.name == item_name), None)
        return item

    def loot_all(self):
        btn_loot_all = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            query={'_name': 'invLootAllBtn'},
            parent_query=self.main_window_query
        ).result
        if not btn_loot_all:
            return False
        click(btn_loot_all)
        return True

    def repair_active_ship(self):
        click(self.active_ship_hangar, MOUSE_RIGHT)
        self.eve_ui.context_menu.click_safe("Get Repair Quote")

        repair_window = wait_for_truthy(lambda: self.eve_ui.ui_tree.find_node(node_type="RepairShopWindow"), 5)

        no_result = None
        repair_all_btn = None
        while not (no_result or repair_all_btn):
            no_result = self.eve_ui.ui_tree.find_node(
                {'_name': 'noResultsContainer'},
                root=repair_window,
                refresh=False
            )
            repair_all_btn = self.eve_ui.ui_tree.find_node(
                {'_setText': "Repair All"},
                node_type="EveLabelMedium",
                root=repair_window,
                refresh=False
            )

        if repair_all_btn:
            click(repair_all_btn)
            pyautogui.press("enter")

        close_btn = self.eve_ui.ui_tree.find_node(
            {'_name': 'CloseButtonIcon'},
            root=repair_window,
            refresh=False
        )
        click(close_btn)
