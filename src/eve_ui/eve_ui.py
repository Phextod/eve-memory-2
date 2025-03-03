import time

from src.eve_ui.agent_window import AgentWindow
from src.eve_ui.context_menu import ContextMenu
from src.eve_ui.drones import Drones
from src.eve_ui.inventory import Inventory
from src.eve_ui.locations import Locations
from src.eve_ui.overview import Overview
from src.eve_ui.route import Route
from src.eve_ui.ship_ui import ShipUI
from src.eve_ui.station_window import StationWindow
from src.eve_ui.target_bar import TargetBar
from src.eve_ui.timers import Timers
from src.utils.ui_tree import UITree


class EveUI:
    def __init__(self):
        start = time.time()
        print("initializing UI tree")
        UITree.instance()
        print(f"UI tree initialized in {time.time() - start}")

        start = time.time()
        print("initializing UI components")
        self.overview = Overview()
        self.target_bar = TargetBar()
        self.ship_ui = ShipUI()
        self.drones = Drones()
        self.inventory = Inventory()
        self.context_menu: ContextMenu = ContextMenu.instance()
        self.locations = Locations()
        self.station_window = StationWindow()
        self.timers = Timers()
        self.route = Route()
        self.agent_window = AgentWindow()
        print(f"UI components initialized in {time.time() - start}")
