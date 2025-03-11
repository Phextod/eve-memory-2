import copy
import itertools
import math
import threading
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
from src.bots.hauler.eve_hauler_v3 import Hauler
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.fleet import Fleet
from src.utils.utils import *

np.seterr(all='raise')


ui = EveUI()
ui_tree: UITree = UITree.instance()
self = AbyssBot(ui)
# self = Hauler(ui)

# abyss_fighter = AbyssFighter(ui)
# abyss_fighter.init_room()
# abyss_fighter.clear_room()

# self.run()
# self.use_filament()
self.do_abyss()

# self.ui.overview.update()
# self.abyss_fighter.clear_room()
#
# clear_order = self.abyss_fighter.calculate_clear_order()
# for stage in clear_order:
#     print(f"target:{stage.target.name}({id(stage.target)},"
#           f" orbit: {stage.orbit_target.name if stage.orbit_target else 'None'}"
#           f"({id(stage.orbit_target) if stage.orbit_target else ''})")
# current_stage, next_stage = self.abyss_fighter.get_current_and_next_stage(clear_order)
#
# self.abyss_fighter.set_orbit_tags(clear_order)
#
# self.abyss_fighter.manage_targeting(current_stage, next_stage)
print("Done")
