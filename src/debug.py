from src.bots.abyss.abyss_bot import AbyssBot
from src.bots.abyss.abyss_fighter import AbyssFighter
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import *

# ui = EveUI()
# self = AbyssBot(ui)
# print("Ready")

AbyssFighter.load_enemy_ships(get_path("data/ships_data.json"))
