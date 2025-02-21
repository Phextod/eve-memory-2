import copy
import itertools
import math
from enum import Enum
from itertools import permutations
from typing import List

import numpy as np
from line_profiler_pycharm import profile

from src.bots.abyss.abyss_bot import AbyssBot
from src.bots.abyss.abyss_fighter import AbyssFighter
from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.fight_plan import FightPlan, Stage
from src.bots.abyss.ship import Ship
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import *

np.seterr(all='raise')

# ui = EveUI()
# ui_tree: UITree = UITree.instance()
# self = AbyssBot(ui)

# self.run()
# self.do_abyss()

# self.use_filament()
# self.do_abyss()


fighter = AbyssFighter()
enemy_types = [
    "Battered Drifter Battleship",
    "Striking Leshak",
    "Battered Drifter Battleship",
    "Striking Leshak",
    "Anchoring Damavik",
    "Anchoring Damavik",
    "Anchoring Damavik",
    "Anchoring Damavik",
    "Anchoring Damavik",
    "Anchoring Damavik",
    "Shining Vila Damavik",
    "Lucid Upholder",
    "Devoted Knight"
]
enemies = [next(copy.deepcopy(e) for e in fighter.enemy_ship_data if e.name == t) for t in enemy_types]


fight_plan = FightPlan(config.ABYSSAL_PLAYER_SHIP, enemies)
best_stages = fight_plan.find_best_plan()

fight_plan._evaluate_stage_order(best_stages)

for i, stage in enumerate(best_stages):
    print(
        f"stage {i:{' '}>2}: target: {stage.target.name:{' '}<30},"
        f" duration:{stage.duration:10.2f},"
        f" orbit_target: {stage.orbit_target.name + f'({id(stage.orbit_target)})' if stage.orbit_target else None}"
    )
print("Done")


