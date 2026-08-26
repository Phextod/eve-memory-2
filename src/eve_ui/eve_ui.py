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
from src.eve_ui.view_3d import View3d
from src.utils.ui_tree import UITree
from src.utils.utils import log
from src.eve_ui.overview import Overview


class EveUI:
    def __init__(self, ui_tree: UITree, do_setup=True):
        self.ui_tree: UITree = ui_tree

        start = time.time()
        log("initializing UI tree")
        log(f"UI tree initialized in {time.time() - start}")

        start = time.time()
        log("initializing UI components")

        self.overview = Overview(self)
        self.target_bar = TargetBar(self)
        self.ship_ui: ShipUI = ShipUI(self)
        self.drones = Drones(self)
        self.inventory = Inventory(self, do_setup=do_setup)
        self.context_menu = ContextMenu(self)
        self.locations = Locations(self, do_setup=do_setup)
        self.station_window = StationWindow(self)
        self.timers = Timers(self)
        self.route = Route(self)
        self.agent_window = AgentWindow(self)
        self.fleet = Fleet(self)
        self.neocom: Neocom = Neocom(self)
        self.view_3d: View3d = View3d(self)

        log(f"UI components initialized in {time.time() - start}")
