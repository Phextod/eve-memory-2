from src.bots.abyss.abyss_bot import AbyssBot
from src.bots.abyss.abyss_fighter import AbyssFighter
from src.bots.abyss.abyss_ship import AbyssShip
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import *

# ui = EveUI()
# self = AbyssBot(ui)
# print("Ready")

ships = AbyssFighter.load_enemy_ships(
    get_path(config.ABYSSAL_SHIP_DATA_PATH),
    get_path(config.ABYSSAL_ITEM_DATA_PATH)
)
print(ships)
