import time

from src.eve_ui.agent_window import AgentWindow
from src.eve_ui.context_menu import ContextMenu
from src.eve_ui.drones import Drones
from src.eve_ui.fleet import Fleet
from src.eve_ui.inventory import Inventory
from src.eve_ui.locations import Locations
from src.eve_ui.neocom import Neocom
from src.eve_ui.route import Route
from src.eve_ui.ship_ui import ShipUI
from src.eve_ui.station_window import StationWindow
from src.eve_ui.target_bar import TargetBar
from src.eve_ui.timers import Timers
from src.utils.ui_tree import UITree
from src.utils.utils import log
from src.eve_ui.overview import Overview


class EveUI:
    def __init__(self, do_setup=True):
        start = time.time()
        log("initializing UI tree")
        UITree.instance()
        log(f"UI tree initialized in {time.time() - start}")

        start = time.time()
        log("initializing UI components")
        self.overview = Overview()
        self.target_bar = TargetBar()
        self.ship_ui: ShipUI = ShipUI.instance()
        self.drones = Drones()
        self.inventory = Inventory(do_setup=do_setup)
        self.context_menu: ContextMenu = ContextMenu.instance()
        self.locations = Locations(do_setup=do_setup)
        self.station_window = StationWindow()
        self.timers = Timers()
        self.route = Route()
        self.agent_window = AgentWindow()
        self.fleet = Fleet()
        self.neocom: Neocom = Neocom.instance()
        log(f"UI components initialized in {time.time() - start}")
