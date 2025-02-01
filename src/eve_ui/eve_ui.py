from src.eve_ui.drones import Drones
from src.eve_ui.inventory import Inventory
from src.eve_ui.overview import Overview
from src.eve_ui.ship_ui import ShipUI
from src.eve_ui.target_bar import TargetBar
from src.utils.interface import UITree


class EveUI:
    def __init__(self, character_name):
        self.ui_tree = UITree(character_name)

        self.overview = Overview(self.ui_tree)
        self.target_bar = TargetBar(self.ui_tree)
        self.ship_ui = ShipUI(self.ui_tree)
        self.drones = Drones(self.ui_tree)
        self.inventory = Inventory(self.ui_tree)
