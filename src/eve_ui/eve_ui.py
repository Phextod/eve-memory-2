import time

from src.eve_ui.context_menu import ContextMenu
from src.eve_ui.drones import Drones
from src.eve_ui.inventory import Inventory
from src.eve_ui.locations import Locations
from src.eve_ui.overview import Overview
from src.eve_ui.ship_ui import ShipUI
from src.eve_ui.station_window import StationWindow
from src.eve_ui.target_bar import TargetBar
from src.utils.interface import UITree


class EveUI:
    def __init__(self, character_name):
        start = time.time()
        print("initializing UI tree")
        self.ui_tree = UITree(character_name)
        print(f"UI tree initialized in {time.time() - start}")

        start = time.time()
        print("initializing UI components")
        self.overview = Overview(self.ui_tree)
        self.target_bar = TargetBar(self.ui_tree)
        self.ship_ui = ShipUI(self.ui_tree)
        self.drones = Drones(self.ui_tree)
        self.inventory = Inventory(self.ui_tree)
        self.context_menu = ContextMenu(self.ui_tree)
        self.locations = Locations(self.ui_tree)
        self.station_window = StationWindow(self.ui_tree)
        print(f"UI components initialized in {time.time() - start}")
