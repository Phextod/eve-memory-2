from src.bots.abyss.abyss_bot import AbyssBot
from src.bots.abyss.abyss_fighter import AbyssFighter
from src.bots.abyss.abyss_ship import AbyssShip
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import *

ui = EveUI()
self = AbyssBot(ui)

# self.run()
# abyss_fighter = AbyssFighter(ui)

self.use_filament()
self.do_abyss()