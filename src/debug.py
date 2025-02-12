import math
from enum import Enum

from src.bots.abyss.abyss_bot import AbyssBot
from src.bots.abyss.abyss_fighter import AbyssFighter
from src.bots.abyss.abyss_ship import AbyssShip
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import *

ui = EveUI()
ui_tree: UITree = UITree.instance()
self = AbyssBot(ui)

self.run()
# self.do_abyss()

# self.use_filament()
# self.repair()
