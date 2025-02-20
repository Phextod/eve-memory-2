import copy
import math
from enum import Enum
from itertools import permutations
from typing import List

from src.bots.abyss.abyss_bot import AbyssBot
from src.bots.abyss.abyss_fighter import AbyssFighter
from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.ship import Ship
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import *


# ui = EveUI()
# ui_tree: UITree = UITree.instance()
# self = AbyssBot(ui)

# self.run()
# self.do_abyss()

# self.use_filament()
# self.do_abyss()

fighter = AbyssFighter()
enemy_types = [
    "Striking Leshak",
]
navigate_target_order = [
    ["Striking Leshak", 1000]
]
best_stages = fighter.calculate_clear_stages(enemy_types, config.ABYSSAL_PLAYER_SHIP, enemy_types[0])

print(best_stages)
#
# for enemy in fighter.enemy_ship_data:
#     if enemy.missile_time_between_shots:
#         continue
#     dps_to_player = enemy.get_dps_to(
#         config.ABYSSAL_PLAYER_SHIP,
#         time_from_start=0,
#         target_distance=15000,
#         target_velocity=config.ABYSSAL_PLAYER_SHIP.max_velocity * 0.5,
#     )
#     print(f"{dps_to_player:.4f} {enemy.name}")

